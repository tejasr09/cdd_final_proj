import os
from datetime import UTC, datetime, timedelta
from urllib.parse import urlparse
from uuid import NAMESPACE_URL, UUID, uuid5

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_engine
from app.models import (
    Dependency,
    Entity,
    EventTrigger,
    OperationalEvent,
    Organization,
    OrganizationMember,
    User,
)

SEED_TIME = datetime(2026, 11, 7, 9, 0, tzinfo=UTC)
SEED_NAMESPACE = "https://ripple-effect.invalid/synthetic-demo/"


def _id(key: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"{SEED_NAMESPACE}{key}")


def _add_if_missing(session: Session, model: type, key: str, **values: object) -> object:
    record_id = _id(key)
    record = session.get(model, record_id)
    if record is None:
        record = model(id=record_id, **values)
        session.add(record)
    return record


def seed_demo_data(session: Session) -> None:
    campus = _add_if_missing(session, Organization, "org-campus", name="North Campus Demo")
    transport = _add_if_missing(session, Organization, "org-transport", name="City Transport Demo")
    session.flush()

    campus_user = _add_if_missing(
        session,
        User,
        "user-campus",
        subject="synthetic:campus-admin",
        display_name="Synthetic Campus Administrator",
    )
    transport_user = _add_if_missing(
        session,
        User,
        "user-transport",
        subject="synthetic:transport-coordinator",
        display_name="Synthetic Transport Coordinator",
    )
    session.flush()

    _add_if_missing(
        session,
        OrganizationMember,
        "member-campus",
        organization_id=campus.id,
        user_id=campus_user.id,
        role="administrator",
        status="active",
    )
    _add_if_missing(
        session,
        OrganizationMember,
        "member-transport",
        organization_id=transport.id,
        user_id=transport_user.id,
        role="operations_coordinator",
        status="active",
    )

    campus_entities = {
        "AC-LAB": ("Advanced Computing Laboratory", "resource", "active"),
        "SESSION-A": ("Practical Session A", "activity", "active"),
        "SESSION-B": ("Practical Session B", "activity", "active"),
        "BATCH-1": ("Student Batch 1", "group", "active"),
        "BATCH-2": ("Student Batch 2", "group", "active"),
        "LAB-B": ("Alternative Laboratory B", "resource", "active"),
        "LAB-C": ("Alternative Laboratory C", "resource", "active"),
        "SLOT-1": ("Afternoon Slot 1", "activity", "active"),
        "SLOT-2": ("Afternoon Slot 2", "activity", "active"),
        "TIMETABLE": ("Shared Timetable", "system", "active"),
        "ARCHIVE-DEMO": ("Archived Synthetic Resource", "resource", "archived"),
    }
    transport_entities = {
        "ROAD-X": ("Road Segment X", "location", "active"),
        "ROUTE-1": ("Bus Route 1", "activity", "active"),
        "ROUTE-2": ("Bus Route 2", "activity", "active"),
        "STOP-A": ("Stop A", "location", "active"),
        "STOP-B": ("Stop B", "location", "active"),
        "COMMUTE-GROUP": ("Commuter Group", "group", "active"),
        "CONNECTION": ("Transfer Connection", "activity", "active"),
        "SCHEDULE": ("Transport Schedule", "system", "active"),
        "ARCHIVE-DEMO": ("Archived Synthetic Stop", "location", "archived"),
    }

    entities: dict[tuple[UUID, str], Entity] = {}
    for organization, records in (
        (campus, campus_entities),
        (transport, transport_entities),
    ):
        for key, (name, entity_type, entity_status) in records.items():
            entity = _add_if_missing(
                session,
                Entity,
                f"entity-{organization.id}-{key}",
                organization_id=organization.id,
                name=name,
                entity_type=entity_type,
                status=entity_status,
                archived_at=SEED_TIME if entity_status == "archived" else None,
            )
            entities[(organization.id, key)] = entity
    session.flush()

    campus_edges = [
        ("AC-LAB", "SESSION-A", "hosts", 0.90, "reviewed"),
        ("AC-LAB", "SESSION-B", "hosts", 0.85, "validated"),
        ("SESSION-A", "BATCH-1", "affects", 0.80, "reviewed"),
        ("SESSION-B", "BATCH-2", "affects", 0.80, "reviewed"),
        ("SESSION-A", "TIMETABLE", "updates", 0.60, "draft"),
        ("SESSION-B", "TIMETABLE", "updates", 0.60, "draft"),
        ("LAB-B", "SLOT-1", "provides_capacity_for", 0.75, "reviewed"),
        ("LAB-C", "SLOT-2", "provides_capacity_for", 0.70, "reviewed"),
        ("TIMETABLE", "SLOT-1", "schedules", 0.50, "draft"),
        ("TIMETABLE", "SLOT-2", "schedules", 0.50, "draft"),
        ("LAB-C", "ARCHIVE-DEMO", "affects", 0.20, "draft"),
    ]
    transport_edges = [
        ("ROAD-X", "ROUTE-1", "affects", 0.90, "reviewed"),
        ("ROAD-X", "ROUTE-2", "affects", 0.70, "draft"),
        ("ROUTE-1", "STOP-A", "serves", 0.80, "reviewed"),
        ("ROUTE-2", "STOP-B", "serves", 0.80, "reviewed"),
        ("STOP-A", "CONNECTION", "enables", 0.65, "draft"),
        ("CONNECTION", "COMMUTE-GROUP", "affects", 0.75, "reviewed"),
        ("ROUTE-1", "SCHEDULE", "updates", 0.50, "draft"),
        ("ROUTE-2", "ARCHIVE-DEMO", "affects", 0.20, "reviewed"),
    ]

    for organization, edges in ((campus, campus_edges), (transport, transport_edges)):
        for index, (source_key, target_key, relation, weight, review) in enumerate(edges):
            is_inactive = index == len(edges) - 1
            valid_from = None
            valid_until = None
            if organization.id == campus.id and index == len(edges) - 1:
                valid_from = SEED_TIME - timedelta(days=30)
                valid_until = SEED_TIME - timedelta(days=1)
            if organization.id == transport.id and index == len(edges) - 1:
                valid_from = SEED_TIME + timedelta(days=30)
            _add_if_missing(
                session,
                Dependency,
                f"dependency-{organization.id}-{source_key}-{target_key}",
                organization_id=organization.id,
                source_entity_id=entities[(organization.id, source_key)].id,
                target_entity_id=entities[(organization.id, target_key)].id,
                relationship_type=relation,
                relationship_label=relation.replace("_", " ").title(),
                weight=weight,
                review_status=review,
                is_active=not is_inactive,
                valid_from=valid_from,
                valid_until=valid_until,
                rationale="Illustrative synthetic demo relationship.",
            )

    campus_event = _add_if_missing(
        session,
        OperationalEvent,
        "event-campus",
        organization_id=campus.id,
        title="Advanced Computing Laboratory unavailable",
        description="Synthetic electrical-maintenance closure for demonstration",
        severity=90,
        start_at=SEED_TIME,
        duration_minutes=3 * 24 * 60,
        status="open",
    )
    transport_event = _add_if_missing(
        session,
        OperationalEvent,
        "event-transport",
        organization_id=transport.id,
        title="Road Segment X closed",
        description="Synthetic road-closure scenario",
        severity=80,
        start_at=SEED_TIME,
        status="open",
    )
    session.flush()

    _add_if_missing(
        session,
        EventTrigger,
        "trigger-campus",
        organization_id=campus.id,
        event_id=campus_event.id,
        entity_id=entities[(campus.id, "AC-LAB")].id,
        exposure=1.0,
    )
    _add_if_missing(
        session,
        EventTrigger,
        "trigger-transport",
        organization_id=transport.id,
        event_id=transport_event.id,
        entity_id=entities[(transport.id, "ROAD-X")].id,
        exposure=1.0,
    )
    session.flush()


def main() -> None:
    environment = os.environ.get("APP_ENV", "production").lower()
    if environment not in {"development", "test"}:
        raise RuntimeError("Synthetic seed data is restricted to APP_ENV=development or test.")

    engine = get_engine()
    if engine.dialect.name != "sqlite":
        hostname = urlparse(str(engine.url)).hostname
        if hostname not in {"localhost", "127.0.0.1", "::1", "db"}:
            raise RuntimeError("Synthetic seed data may only target a local development database.")

    with Session(engine) as session:
        seed_demo_data(session)
        session.commit()
        campus_user = session.scalar(select(User).where(User.subject == "synthetic:campus-admin"))
        transport_user = session.scalar(
            select(User).where(User.subject == "synthetic:transport-coordinator")
        )
        if campus_user is None or transport_user is None:
            raise RuntimeError("The synthetic seed did not create its demo users.")
        print("Inserted or confirmed synthetic demo records in the local database.")
        print(f"North Campus Demo local user ID: {campus_user.id}")
        print(f"City Transport Demo local user ID: {transport_user.id}")


if __name__ == "__main__":
    main()
