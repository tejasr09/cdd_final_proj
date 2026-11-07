import logging
from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth import Permission, authorize
from app.engine import (
    ALGORITHM_VERSION,
    AnalysisInput,
    AnalysisOutput,
    DependencySnapshot,
    EngineInputError,
    EntitySnapshot,
    EventTriggerSnapshot,
    PreparedAnalysis,
    prepare_analysis_input,
    run_analysis,
)
from app.engine import (
    ImpactPath as EnginePath,
)
from app.models import (
    AuditLog,
    Dependency,
    Entity,
    EventTrigger,
    ImpactPath,
    ImpactPathStep,
    ImpactResult,
    ImpactRun,
    OperationalEvent,
    OrganizationMember,
)
from app.schemas import AnalysisRunCreate
from app.services import get_event_for_member

logger = logging.getLogger(__name__)


def _utc_datetime(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _utc_optional_datetime(value: datetime | None) -> datetime | None:
    return _utc_datetime(value) if value is not None else None


def _record_analysis_audit(
    session: Session,
    membership: OrganizationMember,
    run: ImpactRun,
    action: str,
    request_id: str | None,
    summary: dict[str, object],
) -> None:
    session.add(
        AuditLog(
            organization_id=membership.organization_id,
            actor_user_id=membership.user_id,
            action=action,
            resource_type="analysis_run",
            resource_id=run.id,
            request_id=request_id,
            summary=summary,
        )
    )


def _analysis_input(
    event: OperationalEvent,
    triggers: Sequence[EventTrigger],
    entities: Sequence[Entity],
    dependencies: Sequence[Dependency],
    membership: OrganizationMember,
    payload: AnalysisRunCreate,
) -> AnalysisInput:
    trigger_snapshots = tuple(
        EventTriggerSnapshot(
            entity_id=item.entity_id,
            exposure=float(item.exposure),
            rationale=item.rationale,
        )
        for item in triggers
    )
    entity_snapshots = tuple(
        EntitySnapshot(
            id=item.id,
            organization_id=item.organization_id,
            name=item.name,
            entity_type=item.entity_type,
            exposure=float(item.exposure),
            mitigation=float(item.mitigation),
            status=item.status,
        )
        for item in entities
    )
    dependency_snapshots = tuple(
        DependencySnapshot(
            id=item.id,
            organization_id=item.organization_id,
            source_entity_id=item.source_entity_id,
            target_entity_id=item.target_entity_id,
            relationship_type=item.relationship_type,
            relationship_label=item.relationship_label,
            weight=float(item.weight),
            review_status=item.review_status,
            rationale=item.rationale,
            is_active=item.is_active,
            valid_from=_utc_optional_datetime(item.valid_from),
            valid_until=_utc_optional_datetime(item.valid_until),
        )
        for item in dependencies
    )
    return AnalysisInput(
        organization_id=membership.organization_id,
        event_id=event.id,
        event_title=event.title,
        event_status=event.status,
        event_severity=event.severity,
        event_start_at=_utc_datetime(event.start_at),
        triggers=trigger_snapshots,
        entities=entity_snapshots,
        dependencies=dependency_snapshots,
        as_of=payload.as_of,
        max_depth=payload.max_depth,
        min_edge_weight=payload.min_edge_weight,
        depth_attenuation=payload.depth_attenuation,
        aggregation=payload.aggregation,
        max_paths_per_trigger=payload.max_paths_per_trigger,
        max_nodes_per_run=payload.max_nodes_per_run,
        include_trigger_entities=payload.include_trigger_entities,
        algorithm_version=ALGORITHM_VERSION,
    )


def _path_key(path: EnginePath) -> tuple[UUID, tuple[UUID, ...], tuple[UUID, ...]]:
    return path.trigger_entity_id, path.entity_ids, path.dependency_ids


def _path_provenance(path: EnginePath) -> dict[str, object]:
    return {
        "trigger_entity_id": str(path.trigger_entity_id),
        "entity_ids": [str(item) for item in path.entity_ids],
        "dependency_ids": [str(item) for item in path.dependency_ids],
        "entity_names": list(path.entity_names),
        "dependency_labels": list(path.dependency_labels),
        "dependency_types": list(path.dependency_types),
        "weights": list(path.weights),
        "review_statuses": list(path.review_statuses),
        "weakest_review_status": path.weakest_review_status,
        "confidence_value": path.confidence_value,
        "confidence_label": path.confidence_label,
        "trigger_exposure": path.trigger_exposure,
        "trigger_mitigation": path.trigger_mitigation,
        "event_severity": path.event_severity,
        "unrounded_score": path.score,
        "steps": [
            {
                "entity_id": str(step.entity_id),
                "entity_name": step.entity_name,
                "entity_type": step.entity_type,
                "mitigation": step.mitigation,
                "dependency_id": str(step.dependency_id) if step.dependency_id else None,
                "relationship_type": step.relationship_type,
                "relationship_label": step.relationship_label,
                "weight": step.weight,
                "review_status": step.review_status,
                "rationale": step.rationale,
                "is_hypothetical": step.is_hypothetical,
            }
            for step in path.steps
        ],
    }


def _persist_output(
    session: Session,
    membership: OrganizationMember,
    run: ImpactRun,
    output: AnalysisOutput,
) -> None:
    path_models: dict[tuple[UUID, tuple[UUID, ...], tuple[UUID, ...]], ImpactPath] = {}
    primary_path_by_result: dict[UUID, UUID] = {}

    for result in output.results:
        primary_key = _path_key(result.primary_path)
        for path in result.retained_paths:
            path_key = _path_key(path)
            path_model = path_models.get(path_key)
            if path_model is None:
                path_model = ImpactPath(
                    id=uuid4(),
                    organization_id=membership.organization_id,
                    run_id=run.id,
                    entity_id=result.entity_id,
                    trigger_entity_id=path.trigger_entity_id,
                    score=round(path.score, 6),
                    edge_count=path.edge_count,
                    is_primary=path_key == primary_key,
                    provenance=_path_provenance(path),
                )
                path_models[path_key] = path_model
                session.add(path_model)
                for sequence_index, step in enumerate(path.steps):
                    session.add(
                        ImpactPathStep(
                            organization_id=membership.organization_id,
                            path_id=path_model.id,
                            sequence_index=sequence_index,
                            entity_id=step.entity_id,
                            dependency_id=step.dependency_id,
                        )
                    )
            elif path_key == primary_key:
                path_model.is_primary = True
        primary_path_by_result[result.entity_id] = path_models[primary_key].id

    session.flush()
    for result in output.results:
        session.add(
            ImpactResult(
                organization_id=membership.organization_id,
                run_id=run.id,
                entity_id=result.entity_id,
                depth=result.depth,
                score=round(result.score, 6),
                confidence_value=result.confidence_value,
                confidence_label=result.confidence_label,
                primary_path_id=primary_path_by_result[result.entity_id],
                explanation=result.explanation,
                result_flags={
                    "entity_name": result.entity_name,
                    "entity_type": result.entity_type,
                    "impact_level": result.impact_level,
                    "confidence_reason": result.confidence_reason,
                    "trigger_entity_ids": [str(item) for item in result.trigger_entity_ids],
                    "retained_path_count": len(result.retained_paths),
                    "potentially_incomplete": output.status == "completed_with_limits",
                },
            )
        )

    run.status = output.status
    run.algorithm_version = output.algorithm_version
    run.input_hash = output.input_hash
    run.input_snapshot = output.input_snapshot
    run.configuration = output.configuration
    run.as_of = datetime.fromisoformat(str(output.configuration["as_of"]))
    run.summary = {
        "counts": {
            "eligible_nodes": output.counts.eligible_nodes,
            "eligible_edges": output.counts.eligible_edges,
            "visited_nodes": output.counts.visited_nodes,
            "enumerated_paths": output.counts.enumerated_paths,
            "results": len(output.results),
        },
        "trigger_results": [
            {
                "trigger_entity_id": str(item.trigger_entity_id),
                "paths_enumerated": item.paths_enumerated,
                "result_count": len(item.results),
            }
            for item in output.trigger_results
        ],
        "limits": [
            {
                "code": item.code,
                "configured_limit": item.configured_limit,
                "observed": item.observed,
                "omitted": item.omitted,
                "trigger_entity_id": (
                    str(item.trigger_entity_id) if item.trigger_entity_id else None
                ),
            }
            for item in output.limits
        ],
        "warning": output.warning,
    }


def create_analysis_run_for_member(
    session: Session,
    membership: OrganizationMember,
    event_id: UUID,
    payload: AnalysisRunCreate,
    *,
    request_id: str | None = None,
) -> ImpactRun:
    authorize(membership, Permission.ANALYSIS_RUN)
    event = get_event_for_member(session, membership, event_id, for_update=True)
    if event.status != "open":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only open events can be run as live analyses.",
        )

    triggers = list(
        session.scalars(
            select(EventTrigger)
            .where(
                EventTrigger.organization_id == membership.organization_id,
                EventTrigger.event_id == event.id,
            )
            .order_by(EventTrigger.entity_id, EventTrigger.id)
            .with_for_update()
        )
    )
    if not triggers:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An event must have at least one trigger before it can be analyzed.",
        )
    entities = list(
        session.scalars(
            select(Entity)
            .where(Entity.organization_id == membership.organization_id)
            .order_by(Entity.id)
            .with_for_update()
        )
    )
    dependencies = list(
        session.scalars(
            select(Dependency)
            .where(Dependency.organization_id == membership.organization_id)
            .order_by(Dependency.id)
            .with_for_update()
        )
    )
    analysis = _analysis_input(event, triggers, entities, dependencies, membership, payload)
    try:
        prepared: PreparedAnalysis = prepare_analysis_input(analysis)
    except EngineInputError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error

    run = ImpactRun(
        organization_id=membership.organization_id,
        event_id=event.id,
        status="running",
        configuration=prepared.configuration,
        input_snapshot=prepared.input_snapshot,
        algorithm_version=ALGORITHM_VERSION,
        input_hash=prepared.input_hash,
        as_of=prepared.as_of,
        created_by_user_id=membership.user_id,
    )
    session.add(run)
    session.flush()

    try:
        output = run_analysis(analysis)
    except Exception:
        diagnostic_id = str(uuid4())
        run.status = "failed"
        run.summary = {
            "error_code": "engine_execution_failed",
            "diagnostic_id": diagnostic_id,
        }
        _record_analysis_audit(
            session,
            membership,
            run,
            "analysis_run.failed",
            request_id,
            {"error_code": "engine_execution_failed", "diagnostic_id": diagnostic_id},
        )
        logger.exception(
            "Analysis execution failed; run_id=%s diagnostic_id=%s",
            run.id,
            diagnostic_id,
        )
        return run

    _persist_output(session, membership, run, output)
    _record_analysis_audit(
        session,
        membership,
        run,
        "analysis_run.completed"
        if output.status == "completed"
        else "analysis_run.completed_with_limits",
        request_id,
        {
            "status": output.status,
            "input_hash": output.input_hash,
            "result_count": len(output.results),
            "enumerated_paths": output.counts.enumerated_paths,
        },
    )
    return run


def get_analysis_run_for_member(
    session: Session,
    membership: OrganizationMember,
    run_id: UUID,
) -> ImpactRun:
    authorize(membership, Permission.EVENT_READ)
    run = session.scalar(
        select(ImpactRun).where(
            ImpactRun.organization_id == membership.organization_id,
            ImpactRun.id == run_id,
        )
    )
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis run was not found in this organization.",
        )
    return run


def page_analysis_runs_for_member(
    session: Session,
    membership: OrganizationMember,
    *,
    limit: int,
    offset: int,
    event_id: UUID | None = None,
) -> tuple[list[ImpactRun], int]:
    authorize(membership, Permission.EVENT_READ)
    query = select(ImpactRun).where(ImpactRun.organization_id == membership.organization_id)
    if event_id is not None:
        query = query.where(ImpactRun.event_id == event_id)
    total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = list(
        session.scalars(
            query.order_by(ImpactRun.created_at.desc(), ImpactRun.id.desc())
            .limit(limit)
            .offset(offset)
        )
    )
    return items, total


def page_impact_results_for_member(
    session: Session,
    membership: OrganizationMember,
    run_id: UUID,
    *,
    limit: int,
    offset: int,
) -> tuple[list[ImpactResult], int]:
    get_analysis_run_for_member(session, membership, run_id)
    query = select(ImpactResult).where(
        ImpactResult.organization_id == membership.organization_id,
        ImpactResult.run_id == run_id,
    )
    total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = list(
        session.scalars(
            query.order_by(
                ImpactResult.score.desc(),
                ImpactResult.depth,
                ImpactResult.entity_id,
            )
            .limit(limit)
            .offset(offset)
        )
    )
    return items, total


def get_impact_result_for_member(
    session: Session,
    membership: OrganizationMember,
    run_id: UUID,
    entity_id: UUID,
) -> ImpactResult:
    get_analysis_run_for_member(session, membership, run_id)
    result = session.scalar(
        select(ImpactResult).where(
            ImpactResult.organization_id == membership.organization_id,
            ImpactResult.run_id == run_id,
            ImpactResult.entity_id == entity_id,
        )
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Impact result was not found in this analysis run.",
        )
    return result


def page_impact_paths_for_member(
    session: Session,
    membership: OrganizationMember,
    run_id: UUID,
    entity_id: UUID,
    *,
    limit: int,
    offset: int,
) -> tuple[list[ImpactPath], int]:
    get_impact_result_for_member(session, membership, run_id, entity_id)
    query = select(ImpactPath).where(
        ImpactPath.organization_id == membership.organization_id,
        ImpactPath.run_id == run_id,
        ImpactPath.entity_id == entity_id,
    )
    total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = list(
        session.scalars(
            query.order_by(
                ImpactPath.is_primary.desc(),
                ImpactPath.score.desc(),
                ImpactPath.edge_count,
                ImpactPath.id,
            )
            .limit(limit)
            .offset(offset)
        )
    )
    return items, total
