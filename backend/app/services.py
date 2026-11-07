from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.auth import Permission, authorize
from app.models import (
    AuditLog,
    Dependency,
    Entity,
    OperationalEvent,
    OrganizationMember,
)
from app.repositories import get_entity
from app.repositories import list_entities as repository_list_entities


def get_entity_for_member(
    session: Session, membership: OrganizationMember, entity_id: UUID
) -> Entity:
    authorize(membership, Permission.ENTITY_READ)
    entity = get_entity(session, membership.organization_id, entity_id)
    if entity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entity was not found in this organization.",
        )
    return entity


def list_entities_for_member(session: Session, membership: OrganizationMember) -> list[Entity]:
    authorize(membership, Permission.ENTITY_READ)
    return repository_list_entities(session, membership.organization_id)


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


def create_entity(
    session: Session,
    membership: OrganizationMember,
    *,
    name: str,
    entity_type: str,
    description: str | None = None,
    exposure: float = 1.0,
    mitigation: float = 0.0,
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
    name: str | None = None,
    description: str | None = None,
    exposure: float | None = None,
    mitigation: float | None = None,
    request_id: str | None = None,
) -> Entity:
    authorize(membership, Permission.ENTITY_WRITE)
    entity = get_entity_for_member(session, membership, entity_id)
    changed_fields: list[str] = []
    if name is not None:
        if not name.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Entity name must not be empty.",
            )
        entity.name = name.strip()
        changed_fields.append("name")
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
    if not changed_fields:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one entity field must be provided.",
        )
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
    request_id: str | None = None,
) -> Entity:
    authorize(membership, Permission.ENTITY_WRITE)
    entity = get_entity_for_member(session, membership, entity_id)
    if entity.status != "archived":
        entity.status = "archived"
        entity.archived_at = datetime.now(UTC)
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
        status="draft",
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


def create_dependency(
    session: Session,
    membership: OrganizationMember,
    *,
    source_entity_id: UUID,
    target_entity_id: UUID,
    relationship_type: str,
    weight: float,
    rationale: str | None = None,
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
    source = get_entity(session, membership.organization_id, source_entity_id)
    target = get_entity(session, membership.organization_id, target_entity_id)
    if source is None or target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A dependency endpoint was not found in this organization.",
        )
    dependency = Dependency(
        organization_id=membership.organization_id,
        source_entity_id=source.id,
        target_entity_id=target.id,
        relationship_type=relationship_type,
        relationship_label=relationship_type.replace("_", " ").title(),
        weight=weight,
        rationale=rationale,
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
