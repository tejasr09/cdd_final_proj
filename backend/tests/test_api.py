import asyncio
import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest
from httpx import ASGITransport, AsyncClient, Response
from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import Base, get_session, make_engine
from app.engine import analysis_input_from_snapshot, run_analysis
from app.main import app
from app.models import (
    AuditLog,
    Entity,
    ImpactPath,
    ImpactPathStep,
    ImpactResult,
    ImpactRun,
    OperationalEvent,
    Organization,
    OrganizationMember,
    User,
)
from app.seed import seed_demo_data


class ASGIClient:
    def __init__(self, application) -> None:
        self.application = application

    def request(self, method: str, url: str, **kwargs: Any) -> Response:
        async def send_request() -> Response:
            async with AsyncClient(
                transport=ASGITransport(app=self.application),
                base_url="http://testserver",
            ) as client:
                return await client.request(method, url, **kwargs)

        return asyncio.run(send_request())

    def get(self, url: str, **kwargs: Any) -> Response:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> Response:
        return self.request("POST", url, **kwargs)

    def patch(self, url: str, **kwargs: Any) -> Response:
        return self.request("PATCH", url, **kwargs)

    def delete(self, url: str, **kwargs: Any) -> Response:
        return self.request("DELETE", url, **kwargs)


@pytest.fixture
def api_context(tmp_path, monkeypatch) -> Iterator[tuple[ASGIClient, dict[str, str], Engine]]:
    engine = make_engine(f"sqlite:///{tmp_path / 'api.sqlite'}")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        seed_demo_data(session)
        campus = session.scalar(
            select(Organization).where(Organization.name == "North Campus Demo")
        )
        transport = session.scalar(
            select(Organization).where(Organization.name == "City Transport Demo")
        )
        admin = session.scalar(select(User).where(User.subject == "synthetic:campus-admin"))
        transport_coordinator = session.scalar(
            select(User).where(User.subject == "synthetic:transport-coordinator")
        )
        campus_event = session.scalar(
            select(OperationalEvent).where(
                OperationalEvent.title == "Advanced Computing Laboratory unavailable"
            )
        )
        transport_event = session.scalar(
            select(OperationalEvent).where(OperationalEvent.title == "Road Segment X closed")
        )
        laboratory = session.scalar(
            select(Entity).where(Entity.name == "Advanced Computing Laboratory")
        )
        transport_entity = session.scalar(select(Entity).where(Entity.name == "Road Segment X"))
        session.add(User(subject="api-test-analyst", display_name="API Test Analyst"))
        session.add(User(subject="api-test-coordinator", display_name="API Test Coordinator"))
        session.add(User(subject="api-test-department", display_name="API Test Department"))
        session.flush()
        analyst = session.scalar(select(User).where(User.subject == "api-test-analyst"))
        coordinator = session.scalar(select(User).where(User.subject == "api-test-coordinator"))
        department = session.scalar(select(User).where(User.subject == "api-test-department"))
        assert campus is not None
        assert transport is not None
        assert admin is not None
        assert transport_coordinator is not None
        assert laboratory is not None
        assert transport_entity is not None
        assert analyst is not None
        assert coordinator is not None
        assert department is not None
        assert campus_event is not None
        assert transport_event is not None
        session.add_all(
            [
                OrganizationMember(
                    organization_id=campus.id,
                    user_id=analyst.id,
                    role="analyst",
                    status="active",
                ),
                OrganizationMember(
                    organization_id=campus.id,
                    user_id=coordinator.id,
                    role="operations_coordinator",
                    status="active",
                ),
                OrganizationMember(
                    organization_id=campus.id,
                    user_id=department.id,
                    role="department_coordinator",
                    status="active",
                ),
            ]
        )
        session.commit()
        values = {
            "campus_id": str(campus.id),
            "transport_id": str(transport.id),
            "transport_coordinator_id": str(transport_coordinator.id),
            "admin_id": str(admin.id),
            "analyst_id": str(analyst.id),
            "coordinator_id": str(coordinator.id),
            "department_id": str(department.id),
            "laboratory_id": str(laboratory.id),
            "transport_entity_id": str(transport_entity.id),
            "campus_event_id": str(campus_event.id),
            "transport_event_id": str(transport_event.id),
        }

    def override_session() -> Iterator[Session]:
        with Session(engine, expire_on_commit=False) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("ENABLE_LOCAL_AUTH", "true")
    with monkeypatch.context() as environment:
        environment.setenv("APP_ENV", "test")
        environment.setenv("ENABLE_LOCAL_AUTH", "true")
        yield ASGIClient(app), values, engine
    app.dependency_overrides.clear()
    engine.dispose()


def headers(values: dict, *, user: str = "admin", organization: str = "campus") -> dict[str, str]:
    return {
        "X-Local-User-ID": values[f"{user}_id"],
        "X-Active-Organization-ID": values[f"{organization}_id"],
    }


def test_api_errors_use_consistent_envelope_and_request_id(api_context) -> None:
    client, _, _ = api_context

    unauthenticated = client.get("/api/v1/entities")
    assert unauthenticated.status_code == 401
    assert unauthenticated.headers["x-request-id"]
    assert unauthenticated.json()["error"]["code"] == "authentication_error"

    invalid = client.post(
        "/api/v1/entities",
        headers={**headers(api_context[1]), "X-Request-ID": "test-request-123"},
        json={"name": "Bad", "entity_type": "unknown", "unknown": "rejected"},
    )
    assert invalid.status_code == 422
    assert invalid.headers["x-request-id"] == "test-request-123"
    assert invalid.json()["error"]["code"] == "validation_error"
    assert invalid.json()["error"]["details"]
    assert "input" not in invalid.json()["error"]["details"][0]


def test_integrity_errors_return_conflict_envelope(api_context, monkeypatch) -> None:
    client, values, _ = api_context

    def fail_create_entity(*args: Any, **kwargs: Any) -> None:
        raise IntegrityError("INSERT INTO entities", {}, RuntimeError("unique constraint"))

    monkeypatch.setattr("app.api.create_entity", fail_create_entity)
    response = client.post(
        "/api/v1/entities",
        headers={**headers(values), "X-Request-ID": "integrity-conflict-123"},
        json={"name": "Conflicting Entity", "entity_type": "resource"},
    )

    assert response.status_code == 409
    assert response.headers["x-request-id"] == "integrity-conflict-123"
    assert response.json()["error"]["code"] == "conflict"
    assert response.json()["error"]["request_id"] == "integrity-conflict-123"


def test_entity_crud_is_tenant_scoped_authorized_and_audited(api_context) -> None:
    client, values, engine = api_context
    response = client.post(
        "/api/v1/entities",
        headers={**headers(values), "X-Request-ID": "entity-create-123"},
        json={
            "name": "API Test Resource",
            "entity_type": "resource",
            "exposure": 0.8,
            "mitigation": 0.2,
        },
    )
    assert response.status_code == 201
    entity_id = response.json()["id"]
    retrieved = client.get(f"/api/v1/entities/{entity_id}", headers=headers(values))
    assert retrieved.status_code == 200
    assert retrieved.json()["name"] == "API Test Resource"

    listing = client.get(
        "/api/v1/entities?entity_type=resource&limit=1&offset=0",
        headers=headers(values),
    )
    assert listing.status_code == 200
    assert listing.json()["limit"] == 1
    assert listing.json()["offset"] == 0
    assert listing.json()["total"] >= 1
    assert len(listing.json()["items"]) == 1

    updated = client.patch(
        f"/api/v1/entities/{entity_id}",
        headers=headers(values),
        json={
            "mitigation": 0.6,
            "expected_updated_at": response.json()["updated_at"],
        },
    )
    assert updated.status_code == 200
    assert updated.json()["mitigation"] == 0.6
    stale = client.patch(
        f"/api/v1/entities/{entity_id}",
        headers=headers(values),
        json={
            "name": "Stale Update",
            "expected_updated_at": "2000-01-01T00:00:00Z",
        },
    )
    assert stale.status_code == 409

    foreign = client.get(
        f"/api/v1/entities/{entity_id}",
        headers=headers(
            values,
            organization="transport",
            user="transport_coordinator",
        ),
    )
    assert foreign.status_code == 404
    denied = client.post(
        "/api/v1/entities",
        headers=headers(values, user="analyst"),
        json={"name": "Denied", "entity_type": "resource"},
    )
    assert denied.status_code == 403

    archived = client.delete(
        f"/api/v1/entities/{entity_id}",
        headers=headers(values),
        params={"expected_updated_at": updated.json()["updated_at"]},
    )
    assert archived.status_code == 200
    assert archived.json()["status"] == "archived"
    with Session(engine) as session:
        audit_records = list(session.scalars(select(AuditLog)).all())
        actions = {record.action for record in audit_records}
    assert {"entity.created", "entity.updated", "entity.archived"} <= actions
    assert any(
        record.action == "entity.created" and record.request_id == "entity-create-123"
        for record in audit_records
    )


def test_dependency_crud_rejects_duplicate_self_loop_and_cross_tenant(api_context) -> None:
    client, values, engine = api_context
    source_id = values["laboratory_id"]
    target_response = client.post(
        "/api/v1/entities",
        headers=headers(values),
        json={"name": "API Test Target", "entity_type": "activity"},
    )
    target_id = target_response.json()["id"]
    payload = {
        "source_entity_id": source_id,
        "target_entity_id": target_id,
        "relationship_type": "affects",
        "weight": 0.7,
    }
    created = client.post("/api/v1/dependencies", headers=headers(values), json=payload)
    assert created.status_code == 201
    dependency_id = created.json()["id"]
    retrieved = client.get(
        f"/api/v1/dependencies/{dependency_id}",
        headers=headers(values),
    )
    assert retrieved.status_code == 200
    assert retrieved.json()["source_entity_id"] == source_id

    duplicate = client.post("/api/v1/dependencies", headers=headers(values), json=payload)
    assert duplicate.status_code == 409
    self_loop = client.post(
        "/api/v1/dependencies",
        headers=headers(values),
        json={**payload, "target_entity_id": source_id},
    )
    assert self_loop.status_code == 422

    updated = client.patch(
        f"/api/v1/dependencies/{dependency_id}",
        headers=headers(values),
        json={
            "weight": 0.4,
            "expected_updated_at": created.json()["updated_at"],
        },
    )
    assert updated.status_code == 200
    assert updated.json()["weight"] == 0.4
    stale = client.patch(
        f"/api/v1/dependencies/{dependency_id}",
        headers=headers(values),
        json={
            "weight": 0.3,
            "expected_updated_at": created.json()["updated_at"],
        },
    )
    assert stale.status_code == 409
    deactivated = client.patch(
        f"/api/v1/dependencies/{dependency_id}/activation",
        headers=headers(values),
        json={
            "is_active": False,
            "expected_updated_at": updated.json()["updated_at"],
        },
    )
    assert deactivated.status_code == 200
    assert deactivated.json()["is_active"] is False

    cross_tenant = client.post(
        "/api/v1/dependencies",
        headers=headers(values),
        json={
            **payload,
            "target_entity_id": values["transport_entity_id"],
        },
    )
    assert cross_tenant.status_code == 404
    with Session(engine) as session:
        actions = set(session.scalars(select(AuditLog.action)).all())
    assert {
        "dependency.created",
        "dependency.updated",
        "dependency.deactivated",
    } <= actions


def test_event_lifecycle_and_trigger_associations(api_context) -> None:
    client, values, engine = api_context
    created = client.post(
        "/api/v1/events",
        headers=headers(values),
        json={
            "title": "API Test Event",
            "severity": 75,
            "start_at": "2026-11-07T09:00:00Z",
        },
    )
    assert created.status_code == 201
    event_id = created.json()["id"]
    assert created.json()["status"] == "draft"
    event_page = client.get(
        "/api/v1/events?status=draft&limit=1&offset=0",
        headers=headers(values),
    )
    assert event_page.status_code == 200
    assert event_page.json()["total"] >= 1
    updated = client.patch(
        f"/api/v1/events/{event_id}",
        headers=headers(values),
        json={
            "title": "Updated API Test Event",
            "expected_updated_at": created.json()["updated_at"],
        },
    )
    assert updated.status_code == 200
    retrieved = client.get(f"/api/v1/events/{event_id}", headers=headers(values))
    assert retrieved.json()["title"] == "Updated API Test Event"

    invalid_transition = client.patch(
        f"/api/v1/events/{event_id}/status",
        headers=headers(values),
        json={
            "status": "resolved",
            "expected_updated_at": updated.json()["updated_at"],
        },
    )
    assert invalid_transition.status_code == 409

    opened = client.patch(
        f"/api/v1/events/{event_id}/status",
        headers=headers(values),
        json={
            "status": "open",
            "expected_updated_at": updated.json()["updated_at"],
        },
    )
    assert opened.status_code == 200
    cross_tenant_trigger = client.post(
        f"/api/v1/events/{event_id}/triggers",
        headers=headers(values),
        json={"entity_id": values["transport_entity_id"]},
    )
    assert cross_tenant_trigger.status_code == 404
    trigger_payload = {"entity_id": values["laboratory_id"], "exposure": 0.9}
    trigger = client.post(
        f"/api/v1/events/{event_id}/triggers",
        headers=headers(values),
        json=trigger_payload,
    )
    assert trigger.status_code == 201
    trigger_id = trigger.json()["id"]
    duplicate = client.post(
        f"/api/v1/events/{event_id}/triggers",
        headers=headers(values),
        json=trigger_payload,
    )
    assert duplicate.status_code == 409

    trigger_list = client.get(
        f"/api/v1/events/{event_id}/triggers?limit=1",
        headers=headers(values),
    )
    assert trigger_list.status_code == 200
    assert trigger_list.json()["total"] == 1
    removed = client.delete(
        f"/api/v1/events/{event_id}/triggers/{trigger_id}",
        headers=headers(values),
    )
    assert removed.status_code == 204

    resolved = client.patch(
        f"/api/v1/events/{event_id}/status",
        headers=headers(values),
        json={
            "status": "resolved",
            "expected_updated_at": opened.json()["updated_at"],
        },
    )
    assert resolved.status_code == 200
    coordinator_reopen = client.patch(
        f"/api/v1/events/{event_id}/status",
        headers=headers(values, user="coordinator"),
        json={
            "status": "open",
            "expected_updated_at": resolved.json()["updated_at"],
        },
    )
    assert coordinator_reopen.status_code == 403
    reopened = client.patch(
        f"/api/v1/events/{event_id}/status",
        headers=headers(values),
        json={
            "status": "open",
            "expected_updated_at": resolved.json()["updated_at"],
        },
    )
    assert reopened.status_code == 200
    archived = client.patch(
        f"/api/v1/events/{event_id}/status",
        headers=headers(values),
        json={
            "status": "archived",
            "expected_updated_at": reopened.json()["updated_at"],
        },
    )
    assert archived.status_code == 200
    archived_coordinator_reopen = client.patch(
        f"/api/v1/events/{event_id}/status",
        headers=headers(values, user="coordinator"),
        json={
            "status": "open",
            "expected_updated_at": archived.json()["updated_at"],
        },
    )
    assert archived_coordinator_reopen.status_code == 403
    archived_reopened = client.patch(
        f"/api/v1/events/{event_id}/status",
        headers=headers(values),
        json={
            "status": "open",
            "expected_updated_at": archived.json()["updated_at"],
        },
    )
    assert archived_reopened.status_code == 200
    with Session(engine) as session:
        actions = set(session.scalars(select(AuditLog.action)).all())
    assert {
        "event.created",
        "event.status_changed",
        "event_trigger.created",
        "event_trigger.deleted",
    } <= actions


def test_analysis_run_persists_snapshot_results_paths_and_audit(api_context) -> None:
    client, values, engine = api_context
    response = client.post(
        f"/api/v1/events/{values['campus_event_id']}/analysis-runs",
        headers={**headers(values, user="analyst"), "X-Request-ID": "analysis-run-123"},
        json={"max_depth": 4},
    )

    assert response.status_code == 201
    run = response.json()
    assert run["status"] == "completed"
    assert len(run["input_hash"]) == 64
    assert run["algorithm_version"]
    assert run["summary"]["counts"]["eligible_edges"] > 0
    assert run["summary"]["counts"]["enumerated_paths"] > 0

    run_id = run["id"]
    listed_runs = client.get(
        f"/api/v1/analysis-runs?event_id={values['campus_event_id']}",
        headers=headers(values, user="analyst"),
    )
    assert listed_runs.status_code == 200
    assert listed_runs.json()["total"] == 1

    result_page = client.get(
        f"/api/v1/analysis-runs/{run_id}/results?limit=100",
        headers=headers(values, user="analyst"),
    )
    assert result_page.status_code == 200
    session_a = next(
        result
        for result in result_page.json()["items"]
        if result["entity_name"] == "Practical Session A"
    )
    assert session_a["score"] == pytest.approx(64.8)
    assert session_a["impact_level"] == "high"
    assert session_a["confidence_value"] == 0.8
    assert "not the likelihood" in session_a["confidence_reason"]

    paths = client.get(
        f"/api/v1/analysis-runs/{run_id}/results/{session_a['entity_id']}/paths",
        headers=headers(values, user="analyst"),
    )
    assert paths.status_code == 200
    assert paths.json()["total"] == 1
    path = paths.json()["items"][0]
    assert path["is_primary"] is True
    assert path["provenance"]["entity_names"] == [
        "Advanced Computing Laboratory",
        "Practical Session A",
    ]

    with Session(engine) as session:
        persisted_run = session.get(ImpactRun, UUID(run_id))
        persisted_result = session.scalar(
            select(ImpactResult).where(
                ImpactResult.run_id == UUID(run_id),
                ImpactResult.entity_id == UUID(session_a["entity_id"]),
            )
        )
        persisted_path = session.scalar(
            select(ImpactPath).where(
                ImpactPath.run_id == UUID(run_id),
                ImpactPath.entity_id == UUID(session_a["entity_id"]),
            )
        )
        audit = session.scalar(
            select(AuditLog).where(
                AuditLog.action == "analysis_run.completed",
                AuditLog.resource_id == UUID(run_id),
            )
        )
        assert persisted_run is not None
        assert persisted_result is not None
        assert persisted_path is not None
        assert persisted_run.input_snapshot["event"]["id"] == values["campus_event_id"]
        assert persisted_run.input_snapshot["entities"]
        replayed = run_analysis(analysis_input_from_snapshot(persisted_run.input_snapshot))
        replayed_result = next(
            item for item in replayed.results if str(item.entity_id) == session_a["entity_id"]
        )
        assert replayed.input_hash == persisted_run.input_hash
        assert replayed_result.score == persisted_result.score
        assert persisted_path.provenance["weights"] == [0.9]
        assert audit is not None
        assert audit.request_id == "analysis-run-123"
        path_steps = list(
            session.scalars(
                select(ImpactPathStep).where(ImpactPathStep.path_id == persisted_path.id)
            )
        )
        assert [step.sequence_index for step in path_steps] == [0, 1]

        source_entity = session.scalar(
            select(Entity).where(Entity.name == "Advanced Computing Laboratory")
        )
        assert source_entity is not None
        source_entity.name = "Renamed Live Entity"
        session.commit()

    historical_result = client.get(
        f"/api/v1/analysis-runs/{run_id}/results/{session_a['entity_id']}",
        headers=headers(values, user="analyst"),
    )
    assert historical_result.status_code == 200
    assert historical_result.json()["entity_name"] == "Practical Session A"


def test_analysis_run_requires_open_event_trigger_and_run_permission(api_context) -> None:
    client, values, _ = api_context
    denied = client.post(
        f"/api/v1/events/{values['campus_event_id']}/analysis-runs",
        headers=headers(values, user="department"),
        json={},
    )
    assert denied.status_code == 403

    draft = client.post(
        "/api/v1/events",
        headers=headers(values),
        json={
            "title": "Draft analysis event",
            "severity": 50,
            "start_at": "2026-11-07T12:00:00Z",
            "status": "draft",
        },
    )
    assert draft.status_code == 201
    draft_run = client.post(
        f"/api/v1/events/{draft.json()['id']}/analysis-runs",
        headers=headers(values),
        json={},
    )
    assert draft_run.status_code == 409

    open_without_trigger = client.post(
        "/api/v1/events",
        headers=headers(values),
        json={
            "title": "Open event without trigger",
            "severity": 50,
            "start_at": "2026-11-07T12:00:00Z",
            "status": "open",
        },
    )
    assert open_without_trigger.status_code == 201
    missing_trigger = client.post(
        f"/api/v1/events/{open_without_trigger.json()['id']}/analysis-runs",
        headers=headers(values),
        json={},
    )
    assert missing_trigger.status_code == 409


def test_transport_seed_scenario_runs_with_expected_path_and_score(api_context) -> None:
    client, values, _ = api_context
    response = client.post(
        f"/api/v1/events/{values['transport_event_id']}/analysis-runs",
        headers=headers(values, organization="transport", user="transport_coordinator"),
        json={"max_depth": 4},
    )

    assert response.status_code == 201
    assert response.json()["status"] == "completed"
    results = client.get(
        f"/api/v1/analysis-runs/{response.json()['id']}/results?limit=100",
        headers=headers(values, organization="transport", user="transport_coordinator"),
    )
    assert results.status_code == 200
    commute_group = next(
        item for item in results.json()["items"] if item["entity_name"] == "Commuter Group"
    )
    assert commute_group["score"] == pytest.approx(11.501568)
    assert commute_group["confidence_value"] == 0.5
    paths = client.get(
        f"/api/v1/analysis-runs/{response.json()['id']}/results/{commute_group['entity_id']}/paths",
        headers=headers(values, organization="transport", user="transport_coordinator"),
    )
    assert paths.status_code == 200
    assert paths.json()["items"][0]["provenance"]["entity_names"] == [
        "Road Segment X",
        "Bus Route 1",
        "Stop A",
        "Transfer Connection",
        "Commuter Group",
    ]


def test_analysis_runs_are_tenant_scoped_and_failed_run_is_audited(
    api_context,
    monkeypatch,
) -> None:
    client, values, engine = api_context
    campus_run = client.post(
        f"/api/v1/events/{values['campus_event_id']}/analysis-runs",
        headers=headers(values),
        json={},
    )
    assert campus_run.status_code == 201
    foreign = client.get(
        f"/api/v1/analysis-runs/{campus_run.json()['id']}",
        headers=headers(values, organization="transport", user="transport_coordinator"),
    )
    assert foreign.status_code == 404

    def fail_analysis(*args: Any, **kwargs: Any) -> None:
        raise RuntimeError("internal implementation detail")

    monkeypatch.setattr("app.analysis_service.run_analysis", fail_analysis)
    failure = client.post(
        f"/api/v1/events/{values['campus_event_id']}/analysis-runs",
        headers=headers(values),
        json={},
    )
    assert failure.status_code == 500
    assert "internal implementation detail" not in failure.text

    with Session(engine) as session:
        failed_run = session.scalar(
            select(ImpactRun).where(
                ImpactRun.status == "failed",
                ImpactRun.event_id == UUID(values["campus_event_id"]),
            )
        )
        assert failed_run is not None
        assert failed_run.summary["error_code"] == "engine_execution_failed"
        assert failed_run.summary["diagnostic_id"]
        assert failed_run.input_hash
        assert failed_run.input_snapshot
        audit = session.scalar(
            select(AuditLog).where(
                AuditLog.action == "analysis_run.failed",
                AuditLog.resource_id == failed_run.id,
            )
        )
        assert audit is not None


def test_openapi_snapshot_matches_application_contract() -> None:
    snapshot = Path(__file__).parents[2] / "docs" / "api" / "openapi.json"
    assert app.openapi() == json.loads(snapshot.read_text(encoding="utf-8"))
