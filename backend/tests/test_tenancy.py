from collections.abc import Iterator
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import (
    Permission,
    authorize,
    parse_local_user_id,
    resolve_active_membership,
)
from app.database import Base, make_engine
from app.models import (
    AuditLog,
    Dependency,
    Entity,
    EventTrigger,
    OperationalEvent,
    Organization,
    OrganizationMember,
    Scenario,
    ScenarioEntityOverride,
    User,
)
from app.repositories import get_entity, list_entities
from app.services import (
    archive_entity,
    create_dependency,
    create_entity,
    create_event,
    get_entity_for_member,
    update_entity,
)


@pytest.fixture
def session(tmp_path) -> Iterator[Session]:
    engine = make_engine(f"sqlite:///{tmp_path / 'tenancy.db'}")
    Base.metadata.create_all(engine)
    with Session(engine) as db_session:
        yield db_session
    engine.dispose()


def add_member(
    session: Session,
    organization: Organization,
    role: str,
    *,
    status: str = "active",
) -> User:
    user = User(subject=f"local:{role}:{organization.name}:{status}:{uuid4()}")
    session.add(user)
    session.flush()
    session.add(
        OrganizationMember(
            organization_id=organization.id,
            user_id=user.id,
            role=role,
            status=status,
        )
    )
    session.flush()
    return user


def test_tenant_scoped_repository_never_returns_other_organizations_entity(
    session: Session,
) -> None:
    organization_a = Organization(name="Synthetic A")
    organization_b = Organization(name="Synthetic B")
    session.add_all([organization_a, organization_b])
    session.flush()
    entity_a = Entity(
        organization_id=organization_a.id,
        name="A resource",
        entity_type="resource",
    )
    entity_b = Entity(
        organization_id=organization_b.id,
        name="B resource",
        entity_type="resource",
    )
    session.add_all([entity_a, entity_b])
    session.flush()

    assert get_entity(session, organization_b.id, entity_a.id) is None
    assert list_entities(session, organization_b.id) == [entity_b]


def test_database_rejects_cross_tenant_dependency_reference(session: Session) -> None:
    organization_a = Organization(name="Synthetic A")
    organization_b = Organization(name="Synthetic B")
    session.add_all([organization_a, organization_b])
    session.flush()
    entity_a = Entity(
        organization_id=organization_a.id,
        name="A resource",
        entity_type="resource",
    )
    entity_b = Entity(
        organization_id=organization_b.id,
        name="B activity",
        entity_type="activity",
    )
    session.add_all([entity_a, entity_b])
    session.flush()
    session.add(
        Dependency(
            organization_id=organization_b.id,
            source_entity_id=entity_a.id,
            target_entity_id=entity_b.id,
            relationship_type="affects",
            weight=0.8,
        )
    )

    with pytest.raises(IntegrityError):
        session.flush()


def test_database_rejects_cross_tenant_event_trigger(session: Session) -> None:
    organization_a = Organization(name="Synthetic A")
    organization_b = Organization(name="Synthetic B")
    session.add_all([organization_a, organization_b])
    session.flush()
    entity_b = Entity(
        organization_id=organization_b.id,
        name="B activity",
        entity_type="activity",
    )
    event_a = OperationalEvent(
        organization_id=organization_a.id,
        title="A event",
        severity=10,
        start_at=datetime(2026, 11, 7, 9, 0, tzinfo=UTC),
        status="open",
    )
    session.add_all([entity_b, event_a])
    session.flush()

    with pytest.raises(IntegrityError):
        with session.begin_nested():
            session.add(
                EventTrigger(
                    organization_id=organization_b.id,
                    event_id=event_a.id,
                    entity_id=entity_b.id,
                    exposure=1.0,
                )
            )
            session.flush()


def test_event_statuses_match_approved_lifecycle_contract(session: Session) -> None:
    organization = Organization(name="Synthetic lifecycle")
    session.add(organization)
    session.flush()
    start_at = datetime(2026, 11, 7, 9, 0, tzinfo=UTC)
    session.add_all(
        [
            OperationalEvent(
                organization_id=organization.id,
                title=f"Valid {event_status}",
                severity=10,
                start_at=start_at,
                status=event_status,
            )
            for event_status in ("draft", "open", "resolved", "archived")
        ]
    )
    session.flush()

    for event_status in ("closed", "cancelled"):
        with pytest.raises(IntegrityError):
            with session.begin_nested():
                session.add(
                    OperationalEvent(
                        organization_id=organization.id,
                        title=f"Invalid {event_status}",
                        severity=10,
                        start_at=start_at,
                        status=event_status,
                    )
                )
                session.flush()


def test_database_rejects_cross_tenant_scenario_override(session: Session) -> None:
    organization_a = Organization(name="Synthetic A")
    organization_b = Organization(name="Synthetic B")
    session.add_all([organization_a, organization_b])
    session.flush()
    user_b = User(subject="synthetic:b-user")
    entity_a = Entity(
        organization_id=organization_a.id,
        name="A resource",
        entity_type="resource",
    )
    session.add_all([user_b, entity_a])
    session.flush()
    scenario_b = Scenario(
        organization_id=organization_b.id,
        name="B scenario",
        created_by_user_id=user_b.id,
    )
    session.add(scenario_b)
    session.flush()

    with pytest.raises(IntegrityError):
        with session.begin_nested():
            session.add(
                ScenarioEntityOverride(
                    organization_id=organization_b.id,
                    scenario_id=scenario_b.id,
                    entity_id=entity_a.id,
                    exposure=0.5,
                )
            )
            session.flush()


def test_database_rejects_dependency_self_loop_and_invalid_weight(
    session: Session,
) -> None:
    organization = Organization(name="Synthetic")
    session.add(organization)
    session.flush()
    entity = Entity(
        organization_id=organization.id,
        name="Resource",
        entity_type="resource",
    )
    session.add(entity)
    session.flush()

    with pytest.raises(IntegrityError):
        with session.begin_nested():
            session.add(
                Dependency(
                    organization_id=organization.id,
                    source_entity_id=entity.id,
                    target_entity_id=entity.id,
                    relationship_type="affects",
                    relationship_label="Affects",
                    weight=0.8,
                )
            )
            session.flush()

    with pytest.raises(IntegrityError):
        with session.begin_nested():
            session.add(
                Dependency(
                    organization_id=organization.id,
                    source_entity_id=entity.id,
                    target_entity_id=entity.id,
                    relationship_type="affects",
                    relationship_label="Affects",
                    weight=1.5,
                )
            )
            session.flush()


def test_membership_resolution_hides_nonmember_and_inactive_membership(
    session: Session,
) -> None:
    organization = Organization(name="Synthetic")
    other_organization = Organization(name="Other synthetic")
    session.add_all([organization, other_organization])
    session.flush()
    active_user = add_member(session, organization, "analyst")
    inactive_user = add_member(session, organization, "analyst", status="suspended")
    outsider = User(subject="local:outsider")
    session.add(outsider)
    session.flush()

    assert resolve_active_membership(session, active_user.id, organization.id).role == "analyst"
    for user_id in (outsider.id, active_user.id):
        organization_id = other_organization.id if user_id == active_user.id else organization.id
        with pytest.raises(HTTPException) as error:
            resolve_active_membership(session, user_id, organization_id)
        assert error.value.status_code == 404

    with pytest.raises(HTTPException) as error:
        resolve_active_membership(session, inactive_user.id, organization.id)
    assert error.value.status_code == 404


def test_roles_restrict_live_writes_but_allow_analysis_reads(session: Session) -> None:
    organization = Organization(name="Synthetic")
    session.add(organization)
    session.flush()
    analyst = add_member(session, organization, "analyst")
    operations = add_member(session, organization, "operations_coordinator")
    analyst_membership = session.scalar(
        select(OrganizationMember).where(OrganizationMember.user_id == analyst.id)
    )
    operations_membership = session.scalar(
        select(OrganizationMember).where(OrganizationMember.user_id == operations.id)
    )
    assert analyst_membership is not None
    assert operations_membership is not None

    authorize(analyst_membership, Permission.ANALYSIS_RUN)
    authorize(analyst_membership, Permission.ENTITY_READ)
    with pytest.raises(HTTPException) as error:
        authorize(analyst_membership, Permission.ENTITY_WRITE)
    assert error.value.status_code == 403
    authorize(operations_membership, Permission.ENTITY_WRITE)


def test_member_scoped_service_returns_404_for_other_organization(
    session: Session,
) -> None:
    organization_a = Organization(name="Synthetic A")
    organization_b = Organization(name="Synthetic B")
    session.add_all([organization_a, organization_b])
    session.flush()
    user_b = add_member(session, organization_b, "analyst")
    membership_b = session.scalar(
        select(OrganizationMember).where(OrganizationMember.user_id == user_b.id)
    )
    entity_a = Entity(
        organization_id=organization_a.id,
        name="A resource",
        entity_type="resource",
    )
    session.add(entity_a)
    session.flush()
    assert membership_b is not None

    with pytest.raises(HTTPException) as error:
        get_entity_for_member(session, membership_b, entity_a.id)
    assert error.value.status_code == 404


def test_local_auth_requires_opt_in_and_development_or_test_mode(monkeypatch) -> None:
    user_id = uuid4()
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("ENABLE_LOCAL_AUTH", "true")
    assert parse_local_user_id(str(user_id)) == user_id

    monkeypatch.setenv("APP_ENV", "production")
    with pytest.raises(HTTPException) as error:
        parse_local_user_id(str(user_id))
    assert error.value.status_code == 401


def test_analyst_cannot_create_live_entity(session: Session) -> None:
    organization = Organization(name="Synthetic")
    session.add(organization)
    session.flush()
    analyst = add_member(session, organization, "analyst")
    membership = session.scalar(
        select(OrganizationMember).where(OrganizationMember.user_id == analyst.id)
    )
    assert membership is not None

    with pytest.raises(HTTPException) as error:
        create_entity(
            session,
            membership,
            name="Unauthorized change",
            entity_type="resource",
        )
    assert error.value.status_code == 403


def test_authorized_state_changes_write_audit_records(session: Session) -> None:
    organization = Organization(name="Synthetic")
    session.add(organization)
    session.flush()
    user = add_member(session, organization, "operations_coordinator")
    membership = session.scalar(
        select(OrganizationMember).where(OrganizationMember.user_id == user.id)
    )
    assert membership is not None
    target = Entity(
        organization_id=organization.id,
        name="Synthetic session",
        entity_type="activity",
    )
    session.add(target)
    session.flush()

    entity = create_entity(
        session,
        membership,
        name="Lab",
        entity_type="resource",
    )
    event_time = datetime(2026, 11, 7, 9, 0, tzinfo=UTC)
    operational_event = create_event(
        session,
        membership,
        title="Synthetic closure",
        severity=80,
        start_at=event_time,
    )
    update_entity(session, membership, entity.id, name="Updated Lab")
    archive_entity(session, membership, entity.id)
    create_dependency(
        session,
        membership,
        source_entity_id=entity.id,
        target_entity_id=target.id,
        relationship_type="affects",
        weight=0.75,
    )
    session.flush()

    audit_actions = set(session.scalars(select(AuditLog.action)).all())
    assert audit_actions == {
        "entity.created",
        "entity.updated",
        "entity.archived",
        "event.created",
        "dependency.created",
    }
    assert operational_event.organization_id == organization.id
    assert session.scalar(
        select(OperationalEvent).where(OperationalEvent.id == operational_event.id)
    )
