from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import Permission, authorize
from app.models import (
    AuditLog,
    Dependency,
    Entity,
    EventTrigger,
    OperationalEvent,
    OrganizationMember,
)
from app.repositories import (
    get_dependency,
    get_entity,
    get_event,
    get_event_trigger,
    page_dependencies,
    page_entities,
    page_event_triggers,
    page_events,
)
from app.repositories import (
    list_entities as repository_list_entities,
)


def get_entity_for_member(
    session: Session,
    membership: OrganizationMember,
    entity_id: UUID,
    *,
    for_update: bool = False,
) -> Entity:
    authorize(membership, Permission.ENTITY_READ)
    entity = get_entity(
        session,
        membership.organization_id,
        entity_id,
        for_update=for_update,
    )
    if entity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entity was not found in this organization.",
        )
    return entity


def list_entities_for_member(session: Session, membership: OrganizationMember) -> list[Entity]:
    authorize(membership, Permission.ENTITY_READ)
    return repository_list_entities(session, membership.organization_id)


def page_entities_for_member(
    session: Session,
    membership: OrganizationMember,
    *,
    limit: int,
    offset: int,
    entity_type: str | None = None,
    entity_status: str | None = None,
    name: str | None = None,
) -> tuple[list[Entity], int]:
    authorize(membership, Permission.ENTITY_READ)
    return page_entities(
        session,
        membership.organization_id,
        limit=limit,
        offset=offset,
        entity_type=entity_type,
        status=entity_status,
        name=name,
    )


def _record_change(
    session: Session,
    membership: OrganizationMember,
    action: str,
    resource_type: str,
    resource_id: UUID,
    summary: dict[str, str | int | float | bool | None],
    request_id: str | None = None,
) -> None:
    session.add(
        AuditLog(
            organization_id=membership.organization_id,
            actor_user_id=membership.user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            request_id=request_id,
            summary=summary,
        )
    )


def _check_updated_at(current: datetime, expected: datetime | None) -> None:
    if expected is None:
        return
    current_utc = (
        current.replace(tzinfo=UTC)
        if current.tzinfo is None or current.utcoffset() is None
        else current.astimezone(UTC)
    )
    expected_utc = (
        expected.replace(tzinfo=UTC)
        if expected.tzinfo is None or expected.utcoffset() is None
        else expected.astimezone(UTC)
    )
    if current_utc != expected_utc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The resource changed since it was retrieved; reload before updating.",
        )


def create_entity(
    session: Session,
    membership: OrganizationMember,
    *,
    name: str,
    entity_type: str,
    description: str | None = None,
    exposure: float = 1.0,
    mitigation: float = 0.0,
    attributes: dict[str, object] | None = None,
    request_id: str | None = None,
) -> Entity:
    authorize(membership, Permission.ENTITY_WRITE)
    if not name.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Entity name must not be empty.",
        )
    if entity_type not in {
        "person",
        "department",
        "resource",
        "activity",
        "system",
        "location",
        "group",
    }:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Entity type is not supported.",
        )
    if not 0 <= exposure <= 1 or not 0 <= mitigation <= 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Exposure and mitigation must be between 0 and 1.",
        )
    entity = Entity(
        organization_id=membership.organization_id,
        name=name.strip(),
        entity_type=entity_type,
        description=description,
        exposure=exposure,
        mitigation=mitigation,
        attributes=attributes or {},
    )
    session.add(entity)
    session.flush()
    _record_change(
        session,
        membership,
        "entity.created",
        "entity",
        entity.id,
        {"name": entity.name, "entity_type": entity.entity_type},
        request_id,
    )
    return entity


def update_entity(
    session: Session,
    membership: OrganizationMember,
    entity_id: UUID,
    *,
    expected_updated_at: datetime | None = None,
    name: str | None = None,
    entity_type: str | None = None,
    description: str | None = None,
    exposure: float | None = None,
    mitigation: float | None = None,
    attributes: dict[str, object] | None = None,
    request_id: str | None = None,
) -> Entity:
    authorize(membership, Permission.ENTITY_WRITE)
    entity = get_entity_for_member(session, membership, entity_id, for_update=True)
    _check_updated_at(entity.updated_at, expected_updated_at)
    changed_fields: list[str] = []
    if name is not None:
        if not name.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Entity name must not be empty.",
            )
        entity.name = name.strip()
        changed_fields.append("name")
    if entity_type is not None:
        if entity_type not in {
            "person",
            "department",
            "resource",
            "activity",
            "system",
            "location",
            "group",
        }:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Entity type is not supported.",
            )
        entity.entity_type = entity_type
        changed_fields.append("entity_type")
    if description is not None:
        entity.description = description
        changed_fields.append("description")
    if exposure is not None:
        if not 0 <= exposure <= 1:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Exposure must be between 0 and 1.",
            )
        entity.exposure = exposure
        changed_fields.append("exposure")
    if mitigation is not None:
        if not 0 <= mitigation <= 1:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Mitigation must be between 0 and 1.",
            )
        entity.mitigation = mitigation
        changed_fields.append("mitigation")
    if attributes is not None:
        entity.attributes = attributes
        changed_fields.append("attributes")
    if not changed_fields:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one entity field must be provided.",
        )
    entity.updated_at = datetime.now(UTC)
    session.flush()
    _record_change(
        session,
        membership,
        "entity.updated",
        "entity",
        entity.id,
        {"changed_fields": ",".join(changed_fields)},
        request_id,
    )
    return entity


def archive_entity(
    session: Session,
    membership: OrganizationMember,
    entity_id: UUID,
    *,
    expected_updated_at: datetime | None = None,
    request_id: str | None = None,
) -> Entity:
    authorize(membership, Permission.ENTITY_WRITE)
    entity = get_entity_for_member(session, membership, entity_id, for_update=True)
    _check_updated_at(entity.updated_at, expected_updated_at)
    if entity.status != "archived":
        entity.status = "archived"
        entity.archived_at = datetime.now(UTC)
        entity.updated_at = datetime.now(UTC)
        session.flush()
        _record_change(
            session,
            membership,
            "entity.archived",
            "entity",
            entity.id,
            {"status": entity.status},
            request_id,
        )
    return entity


def create_event(
    session: Session,
    membership: OrganizationMember,
    *,
    title: str,
    severity: int,
    start_at: datetime,
    description: str | None = None,
    duration_minutes: int | None = None,
    initial_status: str = "draft",
    request_id: str | None = None,
) -> OperationalEvent:
    authorize(membership, Permission.EVENT_WRITE)
    if not title.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Event title must not be empty.",
        )
    if not 0 <= severity <= 100:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Event severity must be between 0 and 100.",
        )
    if duration_minutes is not None and duration_minutes <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Event duration must be positive.",
        )
    if initial_status not in {"draft", "open"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="New events may only be created as draft or open.",
        )
    if start_at.tzinfo is None or start_at.utcoffset() is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Event start time must include a timezone.",
        )
    operational_event = OperationalEvent(
        organization_id=membership.organization_id,
        title=title.strip(),
        description=description,
        severity=severity,
        start_at=start_at,
        duration_minutes=duration_minutes,
        status=initial_status,
    )
    session.add(operational_event)
    session.flush()
    _record_change(
        session,
        membership,
        "event.created",
        "event",
        operational_event.id,
        {"title": operational_event.title, "severity": operational_event.severity},
        request_id,
    )
    return operational_event


def get_event_for_member(
    session: Session,
    membership: OrganizationMember,
    event_id: UUID,
    *,
    for_update: bool = False,
) -> OperationalEvent:
    authorize(membership, Permission.EVENT_READ)
    operational_event = get_event(
        session,
        membership.organization_id,
        event_id,
        for_update=for_update,
    )
    if operational_event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event was not found in this organization.",
        )
    return operational_event


def page_events_for_member(
    session: Session,
    membership: OrganizationMember,
    *,
    limit: int,
    offset: int,
    event_status: str | None = None,
    title: str | None = None,
    start_from: datetime | None = None,
    start_to: datetime | None = None,
) -> tuple[list[OperationalEvent], int]:
    authorize(membership, Permission.EVENT_READ)
    return page_events(
        session,
        membership.organization_id,
        limit=limit,
        offset=offset,
        status=event_status,
        title=title,
        start_from=start_from,
        start_to=start_to,
    )


def update_event(
    session: Session,
    membership: OrganizationMember,
    event_id: UUID,
    *,
    expected_updated_at: datetime | None = None,
    title: str | None = None,
    description: str | None = None,
    severity: int | None = None,
    start_at: datetime | None = None,
    duration_minutes: int | None = None,
    request_id: str | None = None,
) -> OperationalEvent:
    authorize(membership, Permission.EVENT_WRITE)
    operational_event = get_event_for_member(
        session,
        membership,
        event_id,
        for_update=True,
    )
    _check_updated_at(operational_event.updated_at, expected_updated_at)
    changed_fields: list[str] = []
    if title is not None:
        if not title.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Event title must not be empty.",
            )
        operational_event.title = title.strip()
        changed_fields.append("title")
    if description is not None:
        operational_event.description = description
        changed_fields.append("description")
    if severity is not None:
        if not 0 <= severity <= 100:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Event severity must be between 0 and 100.",
            )
        operational_event.severity = severity
        changed_fields.append("severity")
    if start_at is not None:
        if start_at.tzinfo is None or start_at.utcoffset() is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Event start time must include a timezone.",
            )
        operational_event.start_at = start_at
        changed_fields.append("start_at")
    if duration_minutes is not None:
        if duration_minutes <= 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Event duration must be positive.",
            )
        operational_event.duration_minutes = duration_minutes
        changed_fields.append("duration_minutes")
    if not changed_fields:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one event field must be provided.",
        )
    operational_event.updated_at = datetime.now(UTC)
    session.flush()
    _record_change(
        session,
        membership,
        "event.updated",
        "event",
        operational_event.id,
        {"changed_fields": ",".join(changed_fields)},
        request_id,
    )
    return operational_event


def transition_event_status(
    session: Session,
    membership: OrganizationMember,
    event_id: UUID,
    target_status: str,
    *,
    expected_updated_at: datetime | None = None,
    request_id: str | None = None,
) -> OperationalEvent:
    authorize(membership, Permission.EVENT_WRITE)
    operational_event = get_event_for_member(
        session,
        membership,
        event_id,
        for_update=True,
    )
    _check_updated_at(operational_event.updated_at, expected_updated_at)
    if target_status not in {"open", "resolved", "archived"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unsupported event status transition.",
        )
    current_status = operational_event.status
    if current_status == target_status:
        return operational_event
    if current_status in {"resolved", "archived"} and target_status == "open":
        if membership.role != "administrator":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only an administrator may reopen a resolved or archived event.",
            )
    else:
        allowed_transitions = {
            "draft": {"open", "archived"},
            "open": {"resolved", "archived"},
            "resolved": {"archived"},
            "archived": set(),
        }
        if target_status not in allowed_transitions.get(current_status, set()):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot transition an event from {current_status} to {target_status}.",
            )
    operational_event.status = target_status
    operational_event.updated_at = datetime.now(UTC)
    session.flush()
    _record_change(
        session,
        membership,
        "event.status_changed",
        "event",
        operational_event.id,
        {"from": current_status, "to": target_status},
        request_id,
    )
    return operational_event


def create_dependency(
    session: Session,
    membership: OrganizationMember,
    *,
    source_entity_id: UUID,
    target_entity_id: UUID,
    relationship_type: str,
    relationship_label: str | None = None,
    weight: float,
    rationale: str | None = None,
    review_status: str = "draft",
    is_active: bool = True,
    valid_from: datetime | None = None,
    valid_until: datetime | None = None,
    request_id: str | None = None,
) -> Dependency:
    authorize(membership, Permission.DEPENDENCY_WRITE)
    if source_entity_id == target_entity_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A dependency cannot reference the same source and target.",
        )
    if not relationship_type.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Dependency relationship type must not be empty.",
        )
    if not 0 <= weight <= 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Dependency weight must be between 0 and 1.",
        )
    if review_status not in {"draft", "reviewed", "validated"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Dependency review status is not supported.",
        )
    if valid_from is not None and valid_until is not None and valid_until <= valid_from:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Dependency valid_until must be later than valid_from.",
        )
    source = get_entity(session, membership.organization_id, source_entity_id)
    target = get_entity(session, membership.organization_id, target_entity_id)
    if source is None or target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A dependency endpoint was not found in this organization.",
        )
    duplicate_id = session.scalar(
        select(Dependency.id).where(
            Dependency.organization_id == membership.organization_id,
            Dependency.source_entity_id == source.id,
            Dependency.target_entity_id == target.id,
        )
    )
    if duplicate_id is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A dependency with this source and target already exists.",
        )
    label = relationship_label or relationship_type.replace("_", " ").title()
    if not label.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Dependency relationship label must not be empty.",
        )
    dependency = Dependency(
        organization_id=membership.organization_id,
        source_entity_id=source.id,
        target_entity_id=target.id,
        relationship_type=relationship_type,
        relationship_label=label.strip(),
        weight=weight,
        rationale=rationale,
        review_status=review_status,
        is_active=is_active,
        valid_from=valid_from,
        valid_until=valid_until,
    )
    session.add(dependency)
    session.flush()
    _record_change(
        session,
        membership,
        "dependency.created",
        "dependency",
        dependency.id,
        {
            "source_entity_id": str(source.id),
            "target_entity_id": str(target.id),
            "relationship_type": relationship_type,
            "weight": weight,
        },
        request_id,
    )
    return dependency


def page_dependencies_for_member(
    session: Session,
    membership: OrganizationMember,
    *,
    limit: int,
    offset: int,
    source_entity_id: UUID | None = None,
    target_entity_id: UUID | None = None,
    is_active: bool | None = None,
    review_status: str | None = None,
) -> tuple[list[Dependency], int]:
    authorize(membership, Permission.DEPENDENCY_READ)
    return page_dependencies(
        session,
        membership.organization_id,
        limit=limit,
        offset=offset,
        source_entity_id=source_entity_id,
        target_entity_id=target_entity_id,
        is_active=is_active,
        review_status=review_status,
    )


def get_dependency_for_member(
    session: Session,
    membership: OrganizationMember,
    dependency_id: UUID,
    *,
    for_update: bool = False,
) -> Dependency:
    authorize(membership, Permission.DEPENDENCY_READ)
    dependency = get_dependency(
        session,
        membership.organization_id,
        dependency_id,
        for_update=for_update,
    )
    if dependency is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dependency was not found in this organization.",
        )
    return dependency


def update_dependency(
    session: Session,
    membership: OrganizationMember,
    dependency_id: UUID,
    *,
    expected_updated_at: datetime | None = None,
    source_entity_id: UUID | None = None,
    target_entity_id: UUID | None = None,
    relationship_type: str | None = None,
    relationship_label: str | None = None,
    weight: float | None = None,
    rationale: str | None = None,
    review_status: str | None = None,
    valid_from: datetime | None = None,
    valid_until: datetime | None = None,
    request_id: str | None = None,
) -> Dependency:
    authorize(membership, Permission.DEPENDENCY_WRITE)
    dependency = get_dependency_for_member(
        session,
        membership,
        dependency_id,
        for_update=True,
    )
    _check_updated_at(dependency.updated_at, expected_updated_at)
    changed_fields: list[str] = []
    new_source_id = source_entity_id or dependency.source_entity_id
    new_target_id = target_entity_id or dependency.target_entity_id
    if new_source_id == new_target_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A dependency cannot reference the same source and target.",
        )
    source = get_entity(session, membership.organization_id, new_source_id)
    target = get_entity(session, membership.organization_id, new_target_id)
    if source is None or target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A dependency endpoint was not found in this organization.",
        )
    if (new_source_id, new_target_id) != (
        dependency.source_entity_id,
        dependency.target_entity_id,
    ):
        duplicate_id = session.scalar(
            select(Dependency.id).where(
                Dependency.organization_id == membership.organization_id,
                Dependency.source_entity_id == new_source_id,
                Dependency.target_entity_id == new_target_id,
                Dependency.id != dependency.id,
            )
        )
        if duplicate_id is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A dependency with this source and target already exists.",
            )
        dependency.source_entity_id = new_source_id
        dependency.target_entity_id = new_target_id
        changed_fields.extend(("source_entity_id", "target_entity_id"))
    if relationship_type is not None:
        if not relationship_type.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Dependency relationship type must not be empty.",
            )
        dependency.relationship_type = relationship_type.strip()
        if relationship_label is None:
            dependency.relationship_label = relationship_type.replace("_", " ").title()
        changed_fields.append("relationship_type")
    if relationship_label is not None:
        if not relationship_label.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Dependency relationship label must not be empty.",
            )
        dependency.relationship_label = relationship_label.strip()
        changed_fields.append("relationship_label")
    if weight is not None:
        if not 0 <= weight <= 1:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Dependency weight must be between 0 and 1.",
            )
        dependency.weight = weight
        changed_fields.append("weight")
    if rationale is not None:
        dependency.rationale = rationale
        changed_fields.append("rationale")
    if review_status is not None:
        if review_status not in {"draft", "reviewed", "validated"}:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Dependency review status is not supported.",
            )
        dependency.review_status = review_status
        changed_fields.append("review_status")
    if valid_from is not None:
        dependency.valid_from = valid_from
        changed_fields.append("valid_from")
    if valid_until is not None:
        dependency.valid_until = valid_until
        changed_fields.append("valid_until")
    if (
        dependency.valid_from is not None
        and dependency.valid_until is not None
        and dependency.valid_until <= dependency.valid_from
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Dependency valid_until must be later than valid_from.",
        )
    if not changed_fields:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one dependency field must be provided.",
        )
    dependency.updated_at = datetime.now(UTC)
    session.flush()
    _record_change(
        session,
        membership,
        "dependency.updated",
        "dependency",
        dependency.id,
        {"changed_fields": ",".join(changed_fields)},
        request_id,
    )
    return dependency


def set_dependency_active(
    session: Session,
    membership: OrganizationMember,
    dependency_id: UUID,
    is_active: bool,
    *,
    expected_updated_at: datetime | None = None,
    request_id: str | None = None,
) -> Dependency:
    authorize(membership, Permission.DEPENDENCY_WRITE)
    dependency = get_dependency_for_member(
        session,
        membership,
        dependency_id,
        for_update=True,
    )
    _check_updated_at(dependency.updated_at, expected_updated_at)
    if dependency.is_active != is_active:
        dependency.is_active = is_active
        dependency.updated_at = datetime.now(UTC)
        session.flush()
        _record_change(
            session,
            membership,
            "dependency.activated" if is_active else "dependency.deactivated",
            "dependency",
            dependency.id,
            {"is_active": is_active},
            request_id,
        )
    return dependency


def page_event_triggers_for_member(
    session: Session,
    membership: OrganizationMember,
    event_id: UUID,
    *,
    limit: int,
    offset: int,
) -> tuple[list[EventTrigger], int]:
    get_event_for_member(session, membership, event_id)
    return page_event_triggers(
        session,
        membership.organization_id,
        event_id,
        limit=limit,
        offset=offset,
    )


def create_event_trigger(
    session: Session,
    membership: OrganizationMember,
    event_id: UUID,
    *,
    entity_id: UUID,
    exposure: float = 1.0,
    rationale: str | None = None,
    request_id: str | None = None,
) -> EventTrigger:
    authorize(membership, Permission.EVENT_WRITE)
    get_event_for_member(session, membership, event_id)
    entity = get_entity(session, membership.organization_id, entity_id)
    if entity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trigger entity was not found in this organization.",
        )
    duplicate_id = session.scalar(
        select(EventTrigger.id).where(
            EventTrigger.organization_id == membership.organization_id,
            EventTrigger.event_id == event_id,
            EventTrigger.entity_id == entity_id,
        )
    )
    if duplicate_id is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This event already has the requested trigger entity.",
        )
    if not 0 <= exposure <= 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Trigger exposure must be between 0 and 1.",
        )
    trigger = EventTrigger(
        organization_id=membership.organization_id,
        event_id=event_id,
        entity_id=entity_id,
        exposure=exposure,
        rationale=rationale,
    )
    session.add(trigger)
    session.flush()
    _record_change(
        session,
        membership,
        "event_trigger.created",
        "event_trigger",
        trigger.id,
        {"event_id": str(event_id), "entity_id": str(entity_id)},
        request_id,
    )
    return trigger


def delete_event_trigger(
    session: Session,
    membership: OrganizationMember,
    event_id: UUID,
    trigger_id: UUID,
    *,
    request_id: str | None = None,
) -> None:
    authorize(membership, Permission.EVENT_WRITE)
    get_event_for_member(session, membership, event_id)
    trigger = get_event_trigger(
        session,
        membership.organization_id,
        event_id,
        trigger_id,
    )
    if trigger is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event trigger was not found in this organization.",
        )
    _record_change(
        session,
        membership,
        "event_trigger.deleted",
        "event_trigger",
        trigger.id,
        {"event_id": str(event_id), "entity_id": str(trigger.entity_id)},
        request_id,
    )
    session.delete(trigger)
    session.flush()
