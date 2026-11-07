from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Dependency, Entity, EventTrigger, OperationalEvent


def get_entity(
    session: Session,
    organization_id: UUID,
    entity_id: UUID,
    *,
    for_update: bool = False,
) -> Entity | None:
    query = select(Entity).where(
        Entity.organization_id == organization_id,
        Entity.id == entity_id,
    )
    if for_update:
        query = query.with_for_update()
    return session.scalar(query)


def list_entities(session: Session, organization_id: UUID) -> list[Entity]:
    return list(
        session.scalars(
            select(Entity)
            .where(Entity.organization_id == organization_id)
            .order_by(Entity.name, Entity.id)
        )
    )


def page_entities(
    session: Session,
    organization_id: UUID,
    *,
    limit: int,
    offset: int,
    entity_type: str | None = None,
    status: str | None = None,
    name: str | None = None,
) -> tuple[list[Entity], int]:
    query = select(Entity).where(Entity.organization_id == organization_id)
    if entity_type is not None:
        query = query.where(Entity.entity_type == entity_type)
    if status is not None:
        query = query.where(Entity.status == status)
    if name is not None:
        query = query.where(Entity.name.ilike(f"%{name}%"))
    total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = list(
        session.scalars(query.order_by(Entity.name, Entity.id).limit(limit).offset(offset))
    )
    return items, total


def get_event(
    session: Session,
    organization_id: UUID,
    event_id: UUID,
    *,
    for_update: bool = False,
) -> OperationalEvent | None:
    query = select(OperationalEvent).where(
        OperationalEvent.organization_id == organization_id,
        OperationalEvent.id == event_id,
    )
    if for_update:
        query = query.with_for_update()
    return session.scalar(query)


def page_events(
    session: Session,
    organization_id: UUID,
    *,
    limit: int,
    offset: int,
    status: str | None = None,
    title: str | None = None,
    start_from: datetime | None = None,
    start_to: datetime | None = None,
) -> tuple[list[OperationalEvent], int]:
    query = select(OperationalEvent).where(OperationalEvent.organization_id == organization_id)
    if status is not None:
        query = query.where(OperationalEvent.status == status)
    if title is not None:
        query = query.where(OperationalEvent.title.ilike(f"%{title}%"))
    if start_from is not None:
        query = query.where(OperationalEvent.start_at >= start_from)
    if start_to is not None:
        query = query.where(OperationalEvent.start_at <= start_to)
    total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = list(
        session.scalars(
            query.order_by(OperationalEvent.start_at, OperationalEvent.id)
            .limit(limit)
            .offset(offset)
        )
    )
    return items, total


def list_dependencies(session: Session, organization_id: UUID) -> list[Dependency]:
    return list(
        session.scalars(
            select(Dependency)
            .where(Dependency.organization_id == organization_id)
            .order_by(
                Dependency.source_entity_id,
                Dependency.target_entity_id,
                Dependency.id,
            )
        )
    )


def get_dependency(
    session: Session,
    organization_id: UUID,
    dependency_id: UUID,
    *,
    for_update: bool = False,
) -> Dependency | None:
    query = select(Dependency).where(
        Dependency.organization_id == organization_id,
        Dependency.id == dependency_id,
    )
    if for_update:
        query = query.with_for_update()
    return session.scalar(query)


def page_dependencies(
    session: Session,
    organization_id: UUID,
    *,
    limit: int,
    offset: int,
    source_entity_id: UUID | None = None,
    target_entity_id: UUID | None = None,
    is_active: bool | None = None,
    review_status: str | None = None,
) -> tuple[list[Dependency], int]:
    query = select(Dependency).where(Dependency.organization_id == organization_id)
    if source_entity_id is not None:
        query = query.where(Dependency.source_entity_id == source_entity_id)
    if target_entity_id is not None:
        query = query.where(Dependency.target_entity_id == target_entity_id)
    if is_active is not None:
        query = query.where(Dependency.is_active.is_(is_active))
    if review_status is not None:
        query = query.where(Dependency.review_status == review_status)
    total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = list(
        session.scalars(
            query.order_by(
                Dependency.source_entity_id,
                Dependency.target_entity_id,
                Dependency.id,
            )
            .limit(limit)
            .offset(offset)
        )
    )
    return items, total


def page_event_triggers(
    session: Session,
    organization_id: UUID,
    event_id: UUID,
    *,
    limit: int,
    offset: int,
) -> tuple[list[EventTrigger], int]:
    query = select(EventTrigger).where(
        EventTrigger.organization_id == organization_id,
        EventTrigger.event_id == event_id,
    )
    total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = list(
        session.scalars(
            query.order_by(EventTrigger.entity_id, EventTrigger.id).limit(limit).offset(offset)
        )
    )
    return items, total


def get_event_trigger(
    session: Session,
    organization_id: UUID,
    event_id: UUID,
    trigger_id: UUID,
) -> EventTrigger | None:
    return session.scalar(
        select(EventTrigger).where(
            EventTrigger.organization_id == organization_id,
            EventTrigger.event_id == event_id,
            EventTrigger.id == trigger_id,
        )
    )
