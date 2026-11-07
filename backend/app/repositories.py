from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Dependency, Entity, OperationalEvent


def get_entity(session: Session, organization_id: UUID, entity_id: UUID) -> Entity | None:
    return session.scalar(
        select(Entity).where(
            Entity.organization_id == organization_id,
            Entity.id == entity_id,
        )
    )


def list_entities(session: Session, organization_id: UUID) -> list[Entity]:
    return list(
        session.scalars(
            select(Entity)
            .where(Entity.organization_id == organization_id)
            .order_by(Entity.name, Entity.id)
        )
    )


def get_event(session: Session, organization_id: UUID, event_id: UUID) -> OperationalEvent | None:
    return session.scalar(
        select(OperationalEvent).where(
            OperationalEvent.organization_id == organization_id,
            OperationalEvent.id == event_id,
        )
    )


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
