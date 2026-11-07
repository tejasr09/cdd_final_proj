from __future__ import annotations

import logging
from dataclasses import replace
from datetime import datetime
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.analysis_service import (
    _persist_output,
    _record_analysis_audit,
    get_analysis_run_for_member,
)
from app.auth import Permission, authorize
from app.engine import (
    AnalysisInput,
    DependencySnapshot,
    EngineInputError,
    analysis_input_from_snapshot,
    run_analysis,
)
from app.models import (
    AuditLog,
    Dependency,
    Entity,
    ImpactResult,
    ImpactRun,
    Intervention,
    OrganizationMember,
    Scenario,
    ScenarioDependencyOverride,
    ScenarioEntityOverride,
    ScenarioEvent,
)
from app.schemas import (
    AnalysisRunCreate,
    ScenarioAnalysisRunCreate,
    ScenarioCreate,
    ScenarioEventUpdate,
    ScenarioInterventionCreate,
    ScenarioUpdate,
)

logger = logging.getLogger(__name__)


def _record_scenario_audit(
    session: Session,
    membership: OrganizationMember,
    scenario: Scenario,
    action: str,
    request_id: str | None,
    summary: dict[str, object],
) -> None:
    session.add(
        AuditLog(
            organization_id=membership.organization_id,
            actor_user_id=membership.user_id,
            action=action,
            resource_type="scenario",
            resource_id=scenario.id,
            request_id=request_id,
            summary=summary,
        )
    )


def get_scenario_for_member(
    session: Session,
    membership: OrganizationMember,
    scenario_id: UUID,
    *,
    for_update: bool = False,
) -> Scenario:
    authorize(membership, Permission.EVENT_READ)
    query = select(Scenario).where(
        Scenario.organization_id == membership.organization_id,
        Scenario.id == scenario_id,
    )
    if for_update:
        query = query.with_for_update()
    scenario = session.scalar(query)
    if scenario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scenario was not found in this organization.",
        )
    return scenario


def _require_draft(scenario: Scenario) -> None:
    if scenario.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Archived scenarios cannot be modified or run.",
        )


def _check_version(scenario: Scenario, expected_version: int) -> None:
    if scenario.version != expected_version:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The scenario changed since it was retrieved; reload before updating.",
        )


def _require_baseline_snapshot(run: ImpactRun) -> dict[str, object]:
    if run.scenario_id is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A scenario run cannot be used as a live baseline.",
        )
    if run.status not in {"completed", "completed_with_limits"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only completed live analysis runs can be used as scenario baselines.",
        )
    if not isinstance(run.input_snapshot, dict):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The baseline run does not contain a usable input snapshot.",
        )
    return run.input_snapshot


def create_scenario_for_member(
    session: Session,
    membership: OrganizationMember,
    payload: ScenarioCreate,
    *,
    request_id: str | None = None,
) -> Scenario:
    authorize(membership, Permission.ANALYSIS_RUN)
    baseline = get_analysis_run_for_member(session, membership, payload.baseline_run_id)
    snapshot = _require_baseline_snapshot(baseline)
    event = snapshot.get("event")
    triggers = snapshot.get("triggers")
    if not isinstance(event, dict) or not isinstance(triggers, list):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The baseline run snapshot is missing its event or triggers.",
        )
    scenario = Scenario(
        organization_id=membership.organization_id,
        name=payload.name.strip(),
        description=payload.description,
        baseline_run_id=baseline.id,
        status="draft",
        version=1,
        created_by_user_id=membership.user_id,
    )
    session.add(scenario)
    session.flush()
    session.add(
        ScenarioEvent(
            organization_id=membership.organization_id,
            scenario_id=scenario.id,
            event_id=baseline.event_id,
            event_snapshot={"event": event, "triggers": triggers},
        )
    )
    _record_scenario_audit(
        session,
        membership,
        scenario,
        "scenario.created",
        request_id,
        {"baseline_run_id": str(baseline.id), "version": scenario.version},
    )
    return scenario


def page_scenarios_for_member(
    session: Session,
    membership: OrganizationMember,
    *,
    limit: int,
    offset: int,
) -> tuple[list[Scenario], int]:
    authorize(membership, Permission.EVENT_READ)
    query = select(Scenario).where(Scenario.organization_id == membership.organization_id)
    total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = list(
        session.scalars(
            query.order_by(Scenario.created_at.desc(), Scenario.id.desc())
            .limit(limit)
            .offset(offset)
        )
    )
    return items, total


def get_scenario_detail_for_member(
    session: Session,
    membership: OrganizationMember,
    scenario_id: UUID,
) -> dict[str, object]:
    scenario = get_scenario_for_member(session, membership, scenario_id)
    event_overlay = session.scalar(
        select(ScenarioEvent).where(
            ScenarioEvent.organization_id == membership.organization_id,
            ScenarioEvent.scenario_id == scenario.id,
        )
    )
    if event_overlay is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Scenario event overlay is missing.",
        )
    entity_overrides = list(
        session.scalars(
            select(ScenarioEntityOverride)
            .where(
                ScenarioEntityOverride.organization_id == membership.organization_id,
                ScenarioEntityOverride.scenario_id == scenario.id,
            )
            .order_by(ScenarioEntityOverride.entity_id)
        )
    )
    dependency_overrides = list(
        session.scalars(
            select(ScenarioDependencyOverride)
            .where(
                ScenarioDependencyOverride.organization_id == membership.organization_id,
                ScenarioDependencyOverride.scenario_id == scenario.id,
            )
            .order_by(ScenarioDependencyOverride.id)
        )
    )
    interventions = list(
        session.scalars(
            select(Intervention)
            .where(
                Intervention.organization_id == membership.organization_id,
                Intervention.scenario_id == scenario.id,
            )
            .order_by(Intervention.created_at, Intervention.id)
        )
    )
    return {
        "scenario": scenario,
        "event_overlay": event_overlay.event_snapshot,
        "entity_overrides": entity_overrides,
        "dependency_overrides": dependency_overrides,
        "interventions": interventions,
    }


def update_scenario_for_member(
    session: Session,
    membership: OrganizationMember,
    scenario_id: UUID,
    payload: ScenarioUpdate,
    *,
    request_id: str | None = None,
) -> Scenario:
    authorize(membership, Permission.ANALYSIS_RUN)
    scenario = get_scenario_for_member(session, membership, scenario_id, for_update=True)
    _require_draft(scenario)
    _check_version(scenario, payload.expected_version)
    changes = payload.model_dump(exclude={"expected_version"}, exclude_unset=True)
    for field, value in changes.items():
        setattr(scenario, field, value.strip() if field == "name" else value)
    scenario.version += 1
    _record_scenario_audit(
        session,
        membership,
        scenario,
        "scenario.updated",
        request_id,
        {"version": scenario.version, "changed_fields": sorted(changes)},
    )
    return scenario


def update_scenario_event_for_member(
    session: Session,
    membership: OrganizationMember,
    scenario_id: UUID,
    payload: ScenarioEventUpdate,
    *,
    request_id: str | None = None,
) -> Scenario:
    authorize(membership, Permission.ANALYSIS_RUN)
    scenario = get_scenario_for_member(session, membership, scenario_id, for_update=True)
    _require_draft(scenario)
    _check_version(scenario, payload.expected_version)
    event_overlay = session.scalar(
        select(ScenarioEvent).where(
            ScenarioEvent.organization_id == membership.organization_id,
            ScenarioEvent.scenario_id == scenario.id,
        )
    )
    if event_overlay is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Scenario event overlay is missing.",
        )
    snapshot = dict(event_overlay.event_snapshot)
    event = snapshot.get("event")
    if not isinstance(event, dict):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Scenario event overlay is invalid.",
        )
    updated_event = dict(event)
    changes = payload.model_dump(exclude={"expected_version"}, exclude_unset=True)
    for field, value in changes.items():
        updated_event[field] = value.isoformat() if isinstance(value, datetime) else value
    snapshot["event"] = updated_event
    event_overlay.event_snapshot = snapshot
    scenario.version += 1
    _record_scenario_audit(
        session,
        membership,
        scenario,
        "scenario.event_updated",
        request_id,
        {"version": scenario.version, "changed_fields": sorted(changes)},
    )
    return scenario


def _baseline_ids(snapshot: dict[str, object], collection: str) -> set[UUID]:
    values = snapshot.get(collection)
    if not isinstance(values, list):
        return set()
    result: set[UUID] = set()
    for value in values:
        if isinstance(value, dict) and isinstance(value.get("id"), str):
            try:
                result.add(UUID(value["id"]))
            except ValueError:
                continue
    return result


def create_intervention_for_member(
    session: Session,
    membership: OrganizationMember,
    scenario_id: UUID,
    payload: ScenarioInterventionCreate,
    *,
    request_id: str | None = None,
) -> Intervention:
    authorize(membership, Permission.ANALYSIS_RUN)
    scenario = get_scenario_for_member(session, membership, scenario_id, for_update=True)
    _require_draft(scenario)
    _check_version(scenario, payload.expected_version)
    if scenario.baseline_run_id is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Scenario baseline is missing.",
        )
    baseline = get_analysis_run_for_member(session, membership, scenario.baseline_run_id)
    snapshot = _require_baseline_snapshot(baseline)
    entity_ids = _baseline_ids(snapshot, "entities")
    dependency_ids = _baseline_ids(snapshot, "dependencies")
    target_entity_id = payload.target_entity_id
    target_dependency_id = payload.target_dependency_id

    def require_entity(entity_id: UUID) -> None:
        if entity_id not in entity_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Entity was not present in the scenario baseline.",
            )

    if payload.action_type == "mitigation":
        assert target_entity_id is not None and payload.mitigation is not None
        require_entity(target_entity_id)
        entity = session.scalar(
            select(Entity).where(
                Entity.organization_id == membership.organization_id,
                Entity.id == target_entity_id,
            )
        )
        if entity is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Entity was not found in this organization.",
            )
        override = session.scalar(
            select(ScenarioEntityOverride).where(
                ScenarioEntityOverride.organization_id == membership.organization_id,
                ScenarioEntityOverride.scenario_id == scenario.id,
                ScenarioEntityOverride.entity_id == target_entity_id,
            )
        )
        if override is None:
            override = ScenarioEntityOverride(
                organization_id=membership.organization_id,
                scenario_id=scenario.id,
                entity_id=target_entity_id,
                mitigation=payload.mitigation,
                rationale=payload.rationale,
            )
            session.add(override)
        else:
            override.mitigation = payload.mitigation
            override.rationale = payload.rationale
        target_dependency_id = None
    elif payload.action_type in {"weight_override", "deactivate_dependency"}:
        assert target_dependency_id is not None
        if target_dependency_id not in dependency_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dependency was not present in the scenario baseline.",
            )
        dependency = session.scalar(
            select(Dependency).where(
                Dependency.organization_id == membership.organization_id,
                Dependency.id == target_dependency_id,
            )
        )
        if dependency is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dependency was not found in this organization.",
            )
        override = session.scalar(
            select(ScenarioDependencyOverride).where(
                ScenarioDependencyOverride.organization_id == membership.organization_id,
                ScenarioDependencyOverride.scenario_id == scenario.id,
                ScenarioDependencyOverride.dependency_id == target_dependency_id,
            )
        )
        if override is None:
            override = ScenarioDependencyOverride(
                organization_id=membership.organization_id,
                scenario_id=scenario.id,
                dependency_id=target_dependency_id,
            )
            session.add(override)
        if payload.action_type == "weight_override":
            assert payload.weight is not None
            override.weight = payload.weight
        else:
            override.is_active = False
        override.rationale = payload.rationale
        target_entity_id = None
    else:
        assert (
            target_entity_id is not None
            and payload.source_entity_id is not None
            and payload.weight is not None
            and payload.relationship_type is not None
            and payload.relationship_label is not None
        )
        require_entity(target_entity_id)
        require_entity(payload.source_entity_id)
        scenario_dependency = ScenarioDependencyOverride(
            organization_id=membership.organization_id,
            scenario_id=scenario.id,
            source_entity_id=payload.source_entity_id,
            target_entity_id=target_entity_id,
            relationship_type=payload.relationship_type.strip(),
            relationship_label=payload.relationship_label.strip(),
            weight=payload.weight,
            is_active=True,
            review_status="draft",
            rationale=payload.rationale,
        )
        session.add(scenario_dependency)
        target_dependency_id = None

    intervention = Intervention(
        organization_id=membership.organization_id,
        scenario_id=scenario.id,
        title=payload.title.strip(),
        action_type=payload.action_type,
        target_entity_id=target_entity_id,
        target_dependency_id=target_dependency_id,
        rationale=payload.rationale,
        assumptions=payload.assumptions,
        author_user_id=membership.user_id,
    )
    session.add(intervention)
    scenario.version += 1
    session.flush()
    _record_scenario_audit(
        session,
        membership,
        scenario,
        "scenario.intervention_created",
        request_id,
        {
            "version": scenario.version,
            "intervention_id": str(intervention.id),
            "action_type": intervention.action_type,
        },
    )
    return intervention


def archive_scenario_for_member(
    session: Session,
    membership: OrganizationMember,
    scenario_id: UUID,
    expected_version: int,
    *,
    request_id: str | None = None,
) -> Scenario:
    authorize(membership, Permission.ANALYSIS_RUN)
    scenario = get_scenario_for_member(session, membership, scenario_id, for_update=True)
    _require_draft(scenario)
    _check_version(scenario, expected_version)
    scenario.status = "archived"
    scenario.version += 1
    _record_scenario_audit(
        session,
        membership,
        scenario,
        "scenario.archived",
        request_id,
        {"version": scenario.version},
    )
    return scenario


def _scenario_input(
    session: Session,
    membership: OrganizationMember,
    scenario: Scenario,
    baseline: ImpactRun,
    payload: ScenarioAnalysisRunCreate,
) -> tuple[AnalysisInput, dict[str, object]]:
    baseline_snapshot = _require_baseline_snapshot(baseline)
    try:
        base_analysis = analysis_input_from_snapshot(baseline_snapshot)
    except EngineInputError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The scenario baseline snapshot is invalid.",
        ) from error

    config_fields = set(AnalysisRunCreate.model_fields)
    configuration = {
        key: value for key, value in baseline.configuration.items() if key in config_fields
    }
    configuration.update(payload.model_dump(exclude={"expected_version"}, exclude_none=True))
    try:
        config = AnalysisRunCreate.model_validate(configuration)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The scenario analysis configuration is invalid.",
        ) from error

    event_overlay = session.scalar(
        select(ScenarioEvent).where(
            ScenarioEvent.organization_id == membership.organization_id,
            ScenarioEvent.scenario_id == scenario.id,
        )
    )
    if event_overlay is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Scenario event overlay is missing.",
        )
    event_snapshot = event_overlay.event_snapshot.get("event")
    if not isinstance(event_snapshot, dict):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Scenario event overlay is invalid.",
        )
    try:
        event_start_at = datetime.fromisoformat(str(event_snapshot["start_at"]))
    except (KeyError, ValueError) as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Scenario event start time is invalid.",
        ) from error

    entity_overrides = list(
        session.scalars(
            select(ScenarioEntityOverride).where(
                ScenarioEntityOverride.organization_id == membership.organization_id,
                ScenarioEntityOverride.scenario_id == scenario.id,
            )
        )
    )
    entity_by_id = {entity.id: entity for entity in base_analysis.entities}
    for override in entity_overrides:
        entity = entity_by_id.get(override.entity_id)
        if entity is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Scenario entity overlay is not present in the baseline snapshot.",
            )
        entity_by_id[override.entity_id] = replace(
            entity,
            exposure=override.exposure if override.exposure is not None else entity.exposure,
            mitigation=(
                override.mitigation if override.mitigation is not None else entity.mitigation
            ),
            status=override.status if override.status is not None else entity.status,
        )

    dependency_overrides = list(
        session.scalars(
            select(ScenarioDependencyOverride).where(
                ScenarioDependencyOverride.organization_id == membership.organization_id,
                ScenarioDependencyOverride.scenario_id == scenario.id,
            )
        )
    )
    dependency_by_id = {dependency.id: dependency for dependency in base_analysis.dependencies}
    hypothetical: list[DependencySnapshot] = []
    for override in dependency_overrides:
        if override.dependency_id is not None:
            dependency = dependency_by_id.get(override.dependency_id)
            if dependency is None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Scenario dependency overlay is not present in the baseline snapshot.",
                )
            dependency_by_id[override.dependency_id] = replace(
                dependency,
                weight=override.weight if override.weight is not None else dependency.weight,
                is_active=(
                    override.is_active if override.is_active is not None else dependency.is_active
                ),
                review_status=(
                    override.review_status
                    if override.review_status is not None
                    else dependency.review_status
                ),
                rationale=override.rationale
                if override.rationale is not None
                else dependency.rationale,
            )
        else:
            if (
                override.source_entity_id is None
                or override.target_entity_id is None
                or override.relationship_type is None
                or override.relationship_label is None
                or override.weight is None
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Scenario hypothetical dependency is incomplete.",
                )
            hypothetical.append(
                DependencySnapshot(
                    id=override.id,
                    organization_id=membership.organization_id,
                    source_entity_id=override.source_entity_id,
                    target_entity_id=override.target_entity_id,
                    relationship_type=override.relationship_type,
                    relationship_label=override.relationship_label,
                    weight=override.weight,
                    review_status="draft",
                    rationale=override.rationale,
                    is_active=override.is_active is not False,
                    is_hypothetical=True,
                )
            )

    analysis = replace(
        base_analysis,
        event_title=str(event_snapshot.get("title", base_analysis.event_title)),
        event_status=str(event_snapshot.get("status", base_analysis.event_status)),
        event_severity=int(event_snapshot.get("severity", base_analysis.event_severity)),
        event_start_at=event_start_at,
        entities=tuple(entity_by_id.values()),
        dependencies=tuple(dependency_by_id.values()) + tuple(hypothetical),
        as_of=(
            event_start_at
            if payload.as_of is None and event_start_at != base_analysis.event_start_at
            else config.as_of
        ),
        max_depth=config.max_depth,
        min_edge_weight=config.min_edge_weight,
        depth_attenuation=config.depth_attenuation,
        aggregation=config.aggregation,
        max_paths_per_trigger=config.max_paths_per_trigger,
        max_nodes_per_run=config.max_nodes_per_run,
        include_trigger_entities=config.include_trigger_entities,
    )
    overlay_snapshot = {
        "scenario_id": str(scenario.id),
        "version": scenario.version,
        "baseline_run_id": str(baseline.id),
        "event": event_snapshot,
        "entity_overrides": [
            {
                "entity_id": str(item.entity_id),
                "exposure": item.exposure,
                "mitigation": item.mitigation,
                "status": item.status,
                "rationale": item.rationale,
            }
            for item in entity_overrides
        ],
        "dependency_overrides": [
            {
                "id": str(item.id),
                "dependency_id": str(item.dependency_id) if item.dependency_id else None,
                "source_entity_id": str(item.source_entity_id) if item.source_entity_id else None,
                "target_entity_id": str(item.target_entity_id) if item.target_entity_id else None,
                "relationship_type": item.relationship_type,
                "relationship_label": item.relationship_label,
                "weight": item.weight,
                "is_active": item.is_active,
                "review_status": "draft" if item.dependency_id is None else item.review_status,
                "rationale": item.rationale,
            }
            for item in dependency_overrides
        ],
        "interventions": [
            {
                "id": str(item.id),
                "title": item.title,
                "action_type": item.action_type,
                "target_entity_id": str(item.target_entity_id) if item.target_entity_id else None,
                "target_dependency_id": str(item.target_dependency_id)
                if item.target_dependency_id
                else None,
                "rationale": item.rationale,
                "assumptions": item.assumptions,
                "author_user_id": str(item.author_user_id),
                "created_at": item.created_at.isoformat(),
            }
            for item in session.scalars(
                select(Intervention)
                .where(
                    Intervention.organization_id == membership.organization_id,
                    Intervention.scenario_id == scenario.id,
                )
                .order_by(Intervention.created_at, Intervention.id)
            )
        ],
    }
    return analysis, overlay_snapshot


def create_scenario_analysis_run_for_member(
    session: Session,
    membership: OrganizationMember,
    scenario_id: UUID,
    payload: ScenarioAnalysisRunCreate,
    *,
    request_id: str | None = None,
) -> ImpactRun:
    authorize(membership, Permission.ANALYSIS_RUN)
    scenario = get_scenario_for_member(session, membership, scenario_id, for_update=True)
    _require_draft(scenario)
    _check_version(scenario, payload.expected_version)
    if scenario.baseline_run_id is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Scenario baseline is missing.",
        )
    baseline = get_analysis_run_for_member(session, membership, scenario.baseline_run_id)
    analysis, scenario_snapshot = _scenario_input(
        session,
        membership,
        scenario,
        baseline,
        payload,
    )
    try:
        output = run_analysis(analysis)
    except EngineInputError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error
    except Exception:
        diagnostic_id = str(uuid4())
        failed_run = ImpactRun(
            organization_id=membership.organization_id,
            event_id=baseline.event_id,
            scenario_id=scenario.id,
            status="failed",
            configuration={},
            input_snapshot={"scenario": scenario_snapshot},
            algorithm_version=baseline.algorithm_version,
            input_hash=baseline.input_hash,
            as_of=baseline.as_of,
            summary={"error_code": "scenario_analysis_failed", "diagnostic_id": diagnostic_id},
            created_by_user_id=membership.user_id,
        )
        session.add(failed_run)
        session.flush()
        _record_analysis_audit(
            session,
            membership,
            failed_run,
            "scenario_analysis_run.failed",
            request_id,
            {"error_code": "scenario_analysis_failed", "diagnostic_id": diagnostic_id},
        )
        logger.exception(
            "Scenario analysis failed; run_id=%s diagnostic_id=%s",
            failed_run.id,
            diagnostic_id,
        )
        return failed_run

    input_snapshot = dict(output.input_snapshot)
    input_snapshot["scenario"] = scenario_snapshot
    output = replace(output, input_snapshot=input_snapshot)
    run = ImpactRun(
        organization_id=membership.organization_id,
        event_id=baseline.event_id,
        scenario_id=scenario.id,
        status=output.status,
        configuration=output.configuration,
        input_snapshot=input_snapshot,
        algorithm_version=output.algorithm_version,
        input_hash=output.input_hash,
        as_of=datetime.fromisoformat(str(output.configuration["as_of"])),
        summary={
            "counts": {
                "eligible_nodes": output.counts.eligible_nodes,
                "eligible_edges": output.counts.eligible_edges,
                "visited_nodes": output.counts.visited_nodes,
                "enumerated_paths": output.counts.enumerated_paths,
                "results": len(output.results),
            },
            "warning": output.warning,
            "scenario_version": scenario.version,
            "baseline_run_id": str(baseline.id),
        },
        created_by_user_id=membership.user_id,
    )
    session.add(run)
    session.flush()
    _persist_output(session, membership, run, output)
    run.summary["scenario_version"] = scenario.version
    run.summary["baseline_run_id"] = str(baseline.id)
    _record_analysis_audit(
        session,
        membership,
        run,
        "scenario_analysis_run.completed"
        if output.status == "completed"
        else "scenario_analysis_run.completed_with_limits",
        request_id,
        {
            "scenario_id": str(scenario.id),
            "scenario_version": scenario.version,
            "baseline_run_id": str(baseline.id),
            "status": output.status,
            "input_hash": output.input_hash,
            "result_count": len(output.results),
        },
    )
    _record_scenario_audit(
        session,
        membership,
        scenario,
        "scenario.analysis_run_created",
        request_id,
        {"run_id": str(run.id), "version": scenario.version},
    )
    return run


def compare_scenario_runs_for_member(
    session: Session,
    membership: OrganizationMember,
    scenario_id: UUID,
    scenario_run_id: UUID,
) -> dict[str, object]:
    scenario = get_scenario_for_member(session, membership, scenario_id)
    if scenario.baseline_run_id is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Scenario baseline is missing.",
        )
    baseline = get_analysis_run_for_member(session, membership, scenario.baseline_run_id)
    scenario_run = get_analysis_run_for_member(session, membership, scenario_run_id)
    if scenario_run.scenario_id != scenario.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scenario analysis run was not found for this scenario.",
        )
    if scenario_run.summary.get("baseline_run_id") != str(baseline.id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Scenario run was produced from a different baseline.",
        )
    if baseline.status not in {"completed", "completed_with_limits"} or scenario_run.status not in {
        "completed",
        "completed_with_limits",
    }:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only completed baseline and scenario runs can be compared.",
        )

    def result_map(run_id: UUID) -> dict[UUID, tuple[str, float]]:
        rows = session.scalars(
            select(ImpactResult).where(
                ImpactResult.organization_id == membership.organization_id,
                ImpactResult.run_id == run_id,
            )
        )
        return {
            item.entity_id: (
                str(item.result_flags.get("entity_name", item.entity_id)),
                float(item.score),
            )
            for item in rows
        }

    baseline_results = result_map(baseline.id)
    scenario_results = result_map(scenario_run.id)
    items: list[dict[str, object]] = []
    for entity_id in sorted(set(baseline_results) | set(scenario_results), key=str):
        baseline_value = baseline_results.get(entity_id)
        scenario_value = scenario_results.get(entity_id)
        baseline_score = baseline_value[1] if baseline_value else 0.0
        scenario_score = scenario_value[1] if scenario_value else 0.0
        if baseline_value is None:
            change_type = "added"
        elif scenario_value is None:
            change_type = "removed"
        elif baseline_score != scenario_score:
            change_type = "changed"
        else:
            change_type = "unchanged"
        items.append(
            {
                "entity_id": entity_id,
                "entity_name": (
                    scenario_value[0] if scenario_value is not None else baseline_value[0]
                ),
                "change_type": change_type,
                "baseline_score": baseline_score,
                "scenario_score": scenario_score,
                "delta": round(scenario_score - baseline_score, 6),
            }
        )

    interventions = list(
        session.scalars(
            select(Intervention)
            .where(
                Intervention.organization_id == membership.organization_id,
                Intervention.scenario_id == scenario.id,
            )
            .order_by(Intervention.created_at, Intervention.id)
        )
    )
    return {
        "scenario_id": scenario.id,
        "baseline_run_id": baseline.id,
        "scenario_run_id": scenario_run.id,
        "scenario_version": scenario_run.summary.get("scenario_version", scenario.version),
        "baseline_status": baseline.status,
        "scenario_status": scenario_run.status,
        "potentially_incomplete": (
            baseline.status == "completed_with_limits"
            or scenario_run.status == "completed_with_limits"
        ),
        "estimated_effect": {
            "baseline_total_score": round(
                sum(score for _, score in baseline_results.values()),
                6,
            ),
            "scenario_total_score": round(
                sum(score for _, score in scenario_results.values()),
                6,
            ),
            "score_delta": round(
                sum(score for _, score in baseline_results.values())
                - sum(score for _, score in scenario_results.values()),
                6,
            ),
        },
        "assumptions": interventions,
        "items": items,
    }
