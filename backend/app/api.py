from collections.abc import Sequence
from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.analysis_service import (
    create_analysis_run_for_member,
    get_analysis_run_for_member,
    get_impact_result_for_member,
    page_analysis_runs_for_member,
    page_impact_paths_for_member,
    page_impact_results_for_member,
)
from app.auth import get_active_membership
from app.database import get_session
from app.models import ImpactResult, OrganizationMember
from app.schemas import (
    AnalysisRunCreate,
    AnalysisRunResponse,
    DependencyActivation,
    DependencyCreate,
    DependencyResponse,
    DependencyUpdate,
    EntityCreate,
    EntityResponse,
    EntityStatus,
    EntityType,
    EntityUpdate,
    ErrorEnvelope,
    EventCreate,
    EventResponse,
    EventStatus,
    EventStatusUpdate,
    EventTriggerCreate,
    EventTriggerResponse,
    EventUpdate,
    ImpactPathResponse,
    ImpactResultResponse,
    PageResponse,
    ReviewStatus,
    UTCDateTime,
)
from app.services import (
    archive_entity,
    create_dependency,
    create_entity,
    create_event,
    create_event_trigger,
    delete_event_trigger,
    get_dependency_for_member,
    get_entity_for_member,
    get_event_for_member,
    page_dependencies_for_member,
    page_entities_for_member,
    page_event_triggers_for_member,
    page_events_for_member,
    set_dependency_active,
    transition_event_status,
    update_dependency,
    update_entity,
    update_event,
)

API_ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    code: {"model": ErrorEnvelope, "description": description}
    for code, description in (
        (400, "Invalid request"),
        (401, "Authentication required"),
        (403, "Permission denied"),
        (404, "Resource not found"),
        (409, "State conflict"),
        (422, "Request validation failed"),
        (500, "Internal server error"),
    )
}
router = APIRouter(prefix="/api/v1", responses=API_ERROR_RESPONSES)
SessionDependency = Annotated[Session, Depends(get_session)]
MembershipDependency = Annotated[OrganizationMember, Depends(get_active_membership)]
PageLimit = Annotated[int, Query(ge=1, le=100)]
PageOffset = Annotated[int, Query(ge=0)]


def _request_id(request: Request) -> str:
    return request.state.request_id


def _commit(session: Session) -> None:
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The requested change conflicts with existing data.",
        ) from error


def _page(items: Sequence[object], total: int, limit: int, offset: int) -> dict[str, object]:
    return {"items": items, "limit": limit, "offset": offset, "total": total}


@router.get(
    "/entities",
    response_model=PageResponse[EntityResponse],
    tags=["entities"],
    summary="List organization entities",
    description="Requires entity:read permission. Results use stable name/UUID ordering.",
)
def list_entities_endpoint(
    membership: MembershipDependency,
    session: SessionDependency,
    limit: PageLimit = 50,
    offset: PageOffset = 0,
    entity_type: EntityType | None = None,
    status_filter: Annotated[EntityStatus | None, Query(alias="status")] = None,
    name: Annotated[str | None, Query(min_length=1, max_length=160)] = None,
) -> dict[str, object]:
    items, total = page_entities_for_member(
        session,
        membership,
        limit=limit,
        offset=offset,
        entity_type=entity_type,
        entity_status=status_filter,
        name=name,
    )
    return _page(items, total, limit, offset)


@router.post(
    "/entities",
    response_model=EntityResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["entities"],
    summary="Create an entity",
    description="Requires entity:write permission. The operation and audit record commit together.",
)
def create_entity_endpoint(
    payload: EntityCreate,
    request: Request,
    membership: MembershipDependency,
    session: SessionDependency,
) -> EntityResponse:
    entity = create_entity(
        session,
        membership,
        name=payload.name,
        entity_type=payload.entity_type,
        description=payload.description,
        exposure=payload.exposure,
        mitigation=payload.mitigation,
        attributes=payload.attributes,
        request_id=_request_id(request),
    )
    _commit(session)
    return EntityResponse.model_validate(entity)


@router.get(
    "/entities/{entity_id}",
    response_model=EntityResponse,
    tags=["entities"],
    summary="Retrieve an entity",
    description="Requires entity:read permission. Cross-organization resources return 404.",
)
def get_entity_endpoint(
    entity_id: UUID,
    membership: MembershipDependency,
    session: SessionDependency,
) -> EntityResponse:
    return EntityResponse.model_validate(get_entity_for_member(session, membership, entity_id))


@router.patch(
    "/entities/{entity_id}",
    response_model=EntityResponse,
    tags=["entities"],
    summary="Update an entity",
    description="Requires entity:write permission. Omitted fields remain unchanged.",
)
def update_entity_endpoint(
    entity_id: UUID,
    payload: EntityUpdate,
    request: Request,
    membership: MembershipDependency,
    session: SessionDependency,
) -> EntityResponse:
    changes = payload.model_dump(exclude_unset=True)
    expected_updated_at = changes.pop("expected_updated_at")
    entity = update_entity(
        session,
        membership,
        entity_id,
        expected_updated_at=expected_updated_at,
        **changes,
        request_id=_request_id(request),
    )
    _commit(session)
    return EntityResponse.model_validate(entity)


@router.delete(
    "/entities/{entity_id}",
    response_model=EntityResponse,
    tags=["entities"],
    summary="Archive an entity",
    description="Requires entity:write permission. This is a soft archive, not a physical delete.",
)
def archive_entity_endpoint(
    entity_id: UUID,
    request: Request,
    membership: MembershipDependency,
    session: SessionDependency,
    expected_updated_at: UTCDateTime,
) -> EntityResponse:
    entity = archive_entity(
        session,
        membership,
        entity_id,
        expected_updated_at=expected_updated_at,
        request_id=_request_id(request),
    )
    _commit(session)
    return EntityResponse.model_validate(entity)


@router.get(
    "/dependencies",
    response_model=PageResponse[DependencyResponse],
    tags=["dependencies"],
    summary="List organization dependencies",
    description=(
        "Requires dependency:read permission. Results use stable source/target/UUID ordering."
    ),
)
def list_dependencies_endpoint(
    membership: MembershipDependency,
    session: SessionDependency,
    limit: PageLimit = 50,
    offset: PageOffset = 0,
    source_entity_id: UUID | None = None,
    target_entity_id: UUID | None = None,
    is_active: bool | None = None,
    review_status: ReviewStatus | None = None,
) -> dict[str, object]:
    items, total = page_dependencies_for_member(
        session,
        membership,
        limit=limit,
        offset=offset,
        source_entity_id=source_entity_id,
        target_entity_id=target_entity_id,
        is_active=is_active,
        review_status=review_status,
    )
    return _page(items, total, limit, offset)


@router.post(
    "/dependencies",
    response_model=DependencyResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["dependencies"],
    summary="Create a dependency",
    description=(
        "Requires dependency:write permission. Source and target must be "
        "distinct same-organization entities."
    ),
)
def create_dependency_endpoint(
    payload: DependencyCreate,
    request: Request,
    membership: MembershipDependency,
    session: SessionDependency,
) -> DependencyResponse:
    dependency = create_dependency(
        session,
        membership,
        **payload.model_dump(),
        request_id=_request_id(request),
    )
    _commit(session)
    return DependencyResponse.model_validate(dependency)


@router.get(
    "/dependencies/{dependency_id}",
    response_model=DependencyResponse,
    tags=["dependencies"],
    summary="Retrieve a dependency",
    description="Requires dependency:read permission. Cross-organization resources return 404.",
)
def get_dependency_endpoint(
    dependency_id: UUID,
    membership: MembershipDependency,
    session: SessionDependency,
) -> DependencyResponse:
    return DependencyResponse.model_validate(
        get_dependency_for_member(session, membership, dependency_id)
    )


@router.patch(
    "/dependencies/{dependency_id}",
    response_model=DependencyResponse,
    tags=["dependencies"],
    summary="Update a dependency",
    description="Requires dependency:write permission. Updates retain source-to-target direction.",
)
def update_dependency_endpoint(
    dependency_id: UUID,
    payload: DependencyUpdate,
    request: Request,
    membership: MembershipDependency,
    session: SessionDependency,
) -> DependencyResponse:
    changes = payload.model_dump(exclude_unset=True)
    expected_updated_at = changes.pop("expected_updated_at")
    dependency = update_dependency(
        session,
        membership,
        dependency_id,
        expected_updated_at=expected_updated_at,
        **changes,
        request_id=_request_id(request),
    )
    _commit(session)
    return DependencyResponse.model_validate(dependency)


@router.patch(
    "/dependencies/{dependency_id}/activation",
    response_model=DependencyResponse,
    tags=["dependencies"],
    summary="Activate or deactivate a dependency",
    description="Requires dependency:write permission. Repeated activation changes are idempotent.",
)
def set_dependency_active_endpoint(
    dependency_id: UUID,
    payload: DependencyActivation,
    request: Request,
    membership: MembershipDependency,
    session: SessionDependency,
) -> DependencyResponse:
    dependency = set_dependency_active(
        session,
        membership,
        dependency_id,
        payload.is_active,
        expected_updated_at=payload.expected_updated_at,
        request_id=_request_id(request),
    )
    _commit(session)
    return DependencyResponse.model_validate(dependency)


@router.get(
    "/events",
    response_model=PageResponse[EventResponse],
    tags=["events"],
    summary="List organization events",
    description="Requires event:read permission. Results use stable start-time/UUID ordering.",
)
def list_events_endpoint(
    membership: MembershipDependency,
    session: SessionDependency,
    limit: PageLimit = 50,
    offset: PageOffset = 0,
    status_filter: Annotated[EventStatus | None, Query(alias="status")] = None,
    title: Annotated[str | None, Query(min_length=1, max_length=200)] = None,
    start_from: datetime | None = None,
    start_to: datetime | None = None,
) -> dict[str, object]:
    if start_from is not None and (start_from.tzinfo is None or start_from.utcoffset() is None):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start_from must include a timezone.",
        )
    if start_to is not None and (start_to.tzinfo is None or start_to.utcoffset() is None):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start_to must include a timezone.",
        )
    if start_from is not None and start_to is not None and start_to < start_from:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start_to must not be earlier than start_from.",
        )
    items, total = page_events_for_member(
        session,
        membership,
        limit=limit,
        offset=offset,
        event_status=status_filter,
        title=title,
        start_from=start_from,
        start_to=start_to,
    )
    return _page(items, total, limit, offset)


@router.post(
    "/events",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["events"],
    summary="Create an event",
    description="Requires event:write permission. New events may be draft or open.",
)
def create_event_endpoint(
    payload: EventCreate,
    request: Request,
    membership: MembershipDependency,
    session: SessionDependency,
) -> EventResponse:
    event = create_event(
        session,
        membership,
        title=payload.title,
        description=payload.description,
        severity=payload.severity,
        start_at=payload.start_at,
        duration_minutes=payload.duration_minutes,
        initial_status=payload.status,
        request_id=_request_id(request),
    )
    _commit(session)
    return EventResponse.model_validate(event)


@router.get(
    "/events/{event_id}",
    response_model=EventResponse,
    tags=["events"],
    summary="Retrieve an event",
    description="Requires event:read permission. Cross-organization resources return 404.",
)
def get_event_endpoint(
    event_id: UUID,
    membership: MembershipDependency,
    session: SessionDependency,
) -> EventResponse:
    return EventResponse.model_validate(get_event_for_member(session, membership, event_id))


@router.patch(
    "/events/{event_id}",
    response_model=EventResponse,
    tags=["events"],
    summary="Update an event",
    description=(
        "Requires event:write permission. Change lifecycle state through the status operation."
    ),
)
def update_event_endpoint(
    event_id: UUID,
    payload: EventUpdate,
    request: Request,
    membership: MembershipDependency,
    session: SessionDependency,
) -> EventResponse:
    changes = payload.model_dump(exclude_unset=True)
    expected_updated_at = changes.pop("expected_updated_at")
    event = update_event(
        session,
        membership,
        event_id,
        expected_updated_at=expected_updated_at,
        **changes,
        request_id=_request_id(request),
    )
    _commit(session)
    return EventResponse.model_validate(event)


@router.patch(
    "/events/{event_id}/status",
    response_model=EventResponse,
    tags=["events"],
    summary="Resolve, reopen or archive an event",
    description=(
        "Requires event:write permission. Only administrators may reopen "
        "resolved or archived events."
    ),
)
def update_event_status_endpoint(
    event_id: UUID,
    payload: EventStatusUpdate,
    request: Request,
    membership: MembershipDependency,
    session: SessionDependency,
) -> EventResponse:
    event = transition_event_status(
        session,
        membership,
        event_id,
        payload.status,
        expected_updated_at=payload.expected_updated_at,
        request_id=_request_id(request),
    )
    _commit(session)
    return EventResponse.model_validate(event)


@router.get(
    "/events/{event_id}/triggers",
    response_model=PageResponse[EventTriggerResponse],
    tags=["event triggers"],
    summary="List an event's trigger associations",
    description="Requires event:read permission. Results use stable entity/UUID ordering.",
)
def list_event_triggers_endpoint(
    event_id: UUID,
    membership: MembershipDependency,
    session: SessionDependency,
    limit: PageLimit = 50,
    offset: PageOffset = 0,
) -> dict[str, object]:
    items, total = page_event_triggers_for_member(
        session,
        membership,
        event_id,
        limit=limit,
        offset=offset,
    )
    return _page(items, total, limit, offset)


@router.post(
    "/events/{event_id}/triggers",
    response_model=EventTriggerResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["event triggers"],
    summary="Add an event trigger",
    description=(
        "Requires event:write permission. Event and entity must belong to the active organization."
    ),
)
def create_event_trigger_endpoint(
    event_id: UUID,
    payload: EventTriggerCreate,
    request: Request,
    membership: MembershipDependency,
    session: SessionDependency,
) -> EventTriggerResponse:
    trigger = create_event_trigger(
        session,
        membership,
        event_id,
        entity_id=payload.entity_id,
        exposure=payload.exposure,
        rationale=payload.rationale,
        request_id=_request_id(request),
    )
    _commit(session)
    return EventTriggerResponse.model_validate(trigger)


@router.delete(
    "/events/{event_id}/triggers/{trigger_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["event triggers"],
    summary="Remove an event trigger",
    description="Requires event:write permission. The removal is audit logged.",
)
def delete_event_trigger_endpoint(
    event_id: UUID,
    trigger_id: UUID,
    request: Request,
    membership: MembershipDependency,
    session: SessionDependency,
) -> Response:
    delete_event_trigger(
        session,
        membership,
        event_id,
        trigger_id,
        request_id=_request_id(request),
    )
    _commit(session)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _impact_result_response(result: ImpactResult) -> ImpactResultResponse:
    flags = result.result_flags
    trigger_ids = flags.get("trigger_entity_ids")
    if not isinstance(trigger_ids, list) or not all(isinstance(item, str) for item in trigger_ids):
        raise RuntimeError("Persisted impact result has invalid trigger provenance.")
    return ImpactResultResponse.model_validate(
        {
            "id": result.id,
            "run_id": result.run_id,
            "entity_id": result.entity_id,
            "entity_name": flags.get("entity_name"),
            "entity_type": flags.get("entity_type"),
            "depth": result.depth,
            "score": result.score,
            "impact_level": flags.get("impact_level"),
            "confidence_value": result.confidence_value,
            "confidence_label": result.confidence_label,
            "confidence_reason": flags.get("confidence_reason"),
            "primary_path_id": result.primary_path_id,
            "trigger_entity_ids": trigger_ids,
            "explanation": result.explanation,
            "result_flags": flags,
        }
    )


@router.post(
    "/events/{event_id}/analysis-runs",
    response_model=AnalysisRunResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["analysis"],
    summary="Run an analysis for an open event",
    description=(
        "Requires analysis:run permission. Creates an immutable input snapshot, "
        "persists deterministic results and audit data, and reports safety limits."
    ),
)
def create_analysis_run_endpoint(
    event_id: UUID,
    payload: AnalysisRunCreate,
    request: Request,
    membership: MembershipDependency,
    session: SessionDependency,
) -> AnalysisRunResponse:
    run = create_analysis_run_for_member(
        session,
        membership,
        event_id,
        payload,
        request_id=_request_id(request),
    )
    _commit(session)
    if run.status == "failed":
        diagnostic_id = run.summary.get("diagnostic_id", "unavailable")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed. Diagnostic ID: {diagnostic_id}",
        )
    return AnalysisRunResponse.model_validate(run)


@router.get(
    "/analysis-runs",
    response_model=PageResponse[AnalysisRunResponse],
    tags=["analysis"],
    summary="List analysis runs",
    description="Requires event:read permission. Results use stable creation-time/UUID ordering.",
)
def list_analysis_runs_endpoint(
    membership: MembershipDependency,
    session: SessionDependency,
    limit: PageLimit = 50,
    offset: PageOffset = 0,
    event_id: UUID | None = None,
) -> dict[str, object]:
    items, total = page_analysis_runs_for_member(
        session,
        membership,
        limit=limit,
        offset=offset,
        event_id=event_id,
    )
    return _page(items, total, limit, offset)


@router.get(
    "/analysis-runs/{run_id}",
    response_model=AnalysisRunResponse,
    tags=["analysis"],
    summary="Retrieve an analysis run",
    description="Requires event:read permission; cross-organization runs return 404.",
)
def get_analysis_run_endpoint(
    run_id: UUID,
    membership: MembershipDependency,
    session: SessionDependency,
) -> AnalysisRunResponse:
    return AnalysisRunResponse.model_validate(
        get_analysis_run_for_member(session, membership, run_id)
    )


@router.get(
    "/analysis-runs/{run_id}/results",
    response_model=PageResponse[ImpactResultResponse],
    tags=["analysis"],
    summary="List impact results",
    description="Requires event:read permission. Results are ordered by score, depth and UUID.",
)
def list_impact_results_endpoint(
    run_id: UUID,
    membership: MembershipDependency,
    session: SessionDependency,
    limit: PageLimit = 50,
    offset: PageOffset = 0,
) -> dict[str, object]:
    items, total = page_impact_results_for_member(
        session,
        membership,
        run_id,
        limit=limit,
        offset=offset,
    )
    return _page([_impact_result_response(item) for item in items], total, limit, offset)


@router.get(
    "/analysis-runs/{run_id}/results/{entity_id}",
    response_model=ImpactResultResponse,
    tags=["analysis"],
    summary="Retrieve an impact result",
    description="Returns the immutable entity snapshot and the primary-path explanation.",
)
def get_impact_result_endpoint(
    run_id: UUID,
    entity_id: UUID,
    membership: MembershipDependency,
    session: SessionDependency,
) -> ImpactResultResponse:
    return _impact_result_response(
        get_impact_result_for_member(session, membership, run_id, entity_id)
    )


@router.get(
    "/analysis-runs/{run_id}/results/{entity_id}/paths",
    response_model=PageResponse[ImpactPathResponse],
    tags=["analysis"],
    summary="List retained paths for an impact result",
    description=(
        "Returns primary and retained contributing/alternative paths with immutable "
        "entity and dependency provenance."
    ),
)
def list_impact_paths_endpoint(
    run_id: UUID,
    entity_id: UUID,
    membership: MembershipDependency,
    session: SessionDependency,
    limit: PageLimit = 50,
    offset: PageOffset = 0,
) -> dict[str, object]:
    items, total = page_impact_paths_for_member(
        session,
        membership,
        run_id,
        entity_id,
        limit=limit,
        offset=offset,
    )
    return _page([ImpactPathResponse.model_validate(item) for item in items], total, limit, offset)
