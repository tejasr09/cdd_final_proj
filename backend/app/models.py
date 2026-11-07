from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class Organization(TimestampMixin, Base):
    __tablename__ = "organizations"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(160), nullable=False)


class User(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("subject", name="uq_users_subject"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(160))
    email: Mapped[str | None] = mapped_column(String(320))


class OrganizationMember(TimestampMixin, Base):
    __tablename__ = "organization_members"
    __table_args__ = (
        UniqueConstraint("organization_id", "user_id", name="uq_members_organization_user"),
        CheckConstraint(
            "role IN ('administrator', 'operations_coordinator', "
            "'department_coordinator', 'analyst')",
            name="ck_members_role",
        ),
        CheckConstraint(
            "status IN ('active', 'invited', 'suspended')",
            name="ck_members_status",
        ),
        Index("ix_members_user_organization", "user_id", "organization_id"),
        ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_members_organization",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_members_user",
            ondelete="RESTRICT",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    user_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    role: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")


class Entity(TimestampMixin, Base):
    __tablename__ = "entities"
    __table_args__ = (
        UniqueConstraint("id", "organization_id", name="uq_entities_id_organization"),
        CheckConstraint(
            "entity_type IN ('person', 'department', 'resource', 'activity', "
            "'system', 'location', 'group')",
            name="ck_entities_type",
        ),
        CheckConstraint(
            "status IN ('active', 'inactive', 'archived')",
            name="ck_entities_status",
        ),
        CheckConstraint(
            "exposure >= 0 AND exposure <= 1",
            name="ck_entities_exposure_range",
        ),
        CheckConstraint(
            "mitigation >= 0 AND mitigation <= 1",
            name="ck_entities_mitigation_range",
        ),
        Index(
            "ix_entities_organization_status_type",
            "organization_id",
            "status",
            "entity_type",
        ),
        ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_entities_organization",
            ondelete="CASCADE",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    entity_type: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    exposure: Mapped[float] = mapped_column(nullable=False, default=1.0)
    mitigation: Mapped[float] = mapped_column(nullable=False, default=0.0)
    attributes: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON, nullable=False, default=dict
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Dependency(TimestampMixin, Base):
    __tablename__ = "dependencies"
    __table_args__ = (
        UniqueConstraint("id", "organization_id", name="uq_dependencies_id_organization"),
        UniqueConstraint(
            "organization_id",
            "source_entity_id",
            "target_entity_id",
            name="uq_dependencies_organization_source_target",
        ),
        CheckConstraint("source_entity_id <> target_entity_id", name="ck_dependencies_not_self"),
        CheckConstraint("weight >= 0 AND weight <= 1", name="ck_dependencies_weight_range"),
        CheckConstraint(
            "length(trim(relationship_type)) > 0",
            name="ck_dependencies_relationship_type",
        ),
        CheckConstraint(
            "length(trim(relationship_label)) > 0",
            name="ck_dependencies_relationship_label",
        ),
        CheckConstraint(
            "review_status IN ('draft', 'reviewed', 'validated')",
            name="ck_dependencies_review_status",
        ),
        CheckConstraint(
            "valid_until IS NULL OR valid_from IS NULL OR valid_until > valid_from",
            name="ck_dependencies_validity_window",
        ),
        Index(
            "ix_dependencies_organization_source_active",
            "organization_id",
            "source_entity_id",
            "is_active",
        ),
        Index(
            "ix_dependencies_organization_target",
            "organization_id",
            "target_entity_id",
        ),
        ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_dependencies_organization",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["source_entity_id", "organization_id"],
            ["entities.id", "entities.organization_id"],
            name="fk_dependencies_source_tenant",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["target_entity_id", "organization_id"],
            ["entities.id", "entities.organization_id"],
            name="fk_dependencies_target_tenant",
            ondelete="RESTRICT",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    source_entity_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    target_entity_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(60), nullable=False)
    relationship_label: Mapped[str] = mapped_column(String(80), nullable=False)
    weight: Mapped[float] = mapped_column(nullable=False)
    rationale: Mapped[str | None] = mapped_column(Text)
    review_status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    valid_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class OperationalEvent(TimestampMixin, Base):
    __tablename__ = "events"
    __table_args__ = (
        UniqueConstraint("id", "organization_id", name="uq_events_id_organization"),
        CheckConstraint("severity >= 0 AND severity <= 100", name="ck_events_severity_range"),
        CheckConstraint(
            "duration_minutes IS NULL OR duration_minutes > 0",
            name="ck_events_duration_positive",
        ),
        CheckConstraint(
            "status IN ('draft', 'open', 'resolved', 'archived')",
            name="ck_events_status",
        ),
        Index(
            "ix_events_organization_status_start",
            "organization_id",
            "status",
            "start_at",
        ),
        ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_events_organization",
            ondelete="CASCADE",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    severity: Mapped[int] = mapped_column(Integer, nullable=False)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_minutes: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")


class EventTrigger(Base):
    __tablename__ = "event_triggers"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "event_id",
            "entity_id",
            name="uq_event_triggers_organization_event_entity",
        ),
        CheckConstraint(
            "exposure >= 0 AND exposure <= 1",
            name="ck_event_triggers_exposure_range",
        ),
        Index("ix_event_triggers_organization_event", "organization_id", "event_id"),
        ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_event_triggers_organization",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["event_id", "organization_id"],
            ["events.id", "events.organization_id"],
            name="fk_event_triggers_event_tenant",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["entity_id", "organization_id"],
            ["entities.id", "entities.organization_id"],
            name="fk_event_triggers_entity_tenant",
            ondelete="RESTRICT",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    event_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    entity_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    exposure: Mapped[float] = mapped_column(nullable=False, default=1.0)
    rationale: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class Scenario(TimestampMixin, Base):
    __tablename__ = "scenarios"
    __table_args__ = (
        UniqueConstraint("id", "organization_id", name="uq_scenarios_id_organization"),
        CheckConstraint("status IN ('draft', 'archived')", name="ck_scenarios_status"),
        CheckConstraint("version >= 1", name="ck_scenarios_version_positive"),
        Index(
            "ix_scenarios_organization_created",
            "organization_id",
            "created_at",
        ),
        ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_scenarios_organization",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            name="fk_scenarios_creator",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["baseline_run_id", "organization_id"],
            ["impact_runs.id", "impact_runs.organization_id"],
            name="fk_scenarios_baseline_run_tenant",
            ondelete="RESTRICT",
            use_alter=True,
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    baseline_run_id: Mapped[UUID | None] = mapped_column(Uuid)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_by_user_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)


class ImpactRun(TimestampMixin, Base):
    __tablename__ = "impact_runs"
    __table_args__ = (
        UniqueConstraint("id", "organization_id", name="uq_impact_runs_id_organization"),
        CheckConstraint(
            "status IN ('pending', 'running', 'completed', 'completed_with_limits', "
            "'incomplete', 'failed')",
            name="ck_impact_runs_status",
        ),
        Index(
            "ix_impact_runs_organization_created",
            "organization_id",
            "created_at",
        ),
        Index(
            "ix_impact_runs_organization_event",
            "organization_id",
            "event_id",
        ),
        ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_impact_runs_organization",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["event_id", "organization_id"],
            ["events.id", "events.organization_id"],
            name="fk_impact_runs_event_tenant",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["scenario_id", "organization_id"],
            ["scenarios.id", "scenarios.organization_id"],
            name="fk_impact_runs_scenario_tenant",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            name="fk_impact_runs_creator",
            ondelete="RESTRICT",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    event_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    scenario_id: Mapped[UUID | None] = mapped_column(Uuid)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    configuration: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    input_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    algorithm_version: Mapped[str] = mapped_column(String(80), nullable=False)
    input_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    summary: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_by_user_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)


class ImpactPath(TimestampMixin, Base):
    __tablename__ = "impact_paths"
    __table_args__ = (
        UniqueConstraint("id", "organization_id", name="uq_impact_paths_id_organization"),
        UniqueConstraint(
            "id",
            "organization_id",
            "run_id",
            "entity_id",
            name="uq_impact_paths_run_entity",
        ),
        CheckConstraint("score >= 0 AND score <= 100", name="ck_impact_paths_score_range"),
        CheckConstraint("edge_count >= 0", name="ck_impact_paths_edge_count_nonnegative"),
        Index(
            "ix_impact_paths_organization_run_entity",
            "organization_id",
            "run_id",
            "entity_id",
        ),
        ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_impact_paths_organization",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["run_id", "organization_id"],
            ["impact_runs.id", "impact_runs.organization_id"],
            name="fk_impact_paths_run_tenant",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["entity_id", "organization_id"],
            ["entities.id", "entities.organization_id"],
            name="fk_impact_paths_entity_tenant",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["trigger_entity_id", "organization_id"],
            ["entities.id", "entities.organization_id"],
            name="fk_impact_paths_trigger_tenant",
            ondelete="RESTRICT",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    run_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    entity_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    trigger_entity_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    score: Mapped[float] = mapped_column(nullable=False)
    edge_count: Mapped[int] = mapped_column(Integer, nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)


class ImpactPathStep(Base):
    __tablename__ = "impact_path_steps"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "path_id",
            "sequence_index",
            name="uq_impact_path_steps_order",
        ),
        CheckConstraint("sequence_index >= 0", name="ck_impact_path_steps_index_nonnegative"),
        ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_impact_path_steps_organization",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["path_id", "organization_id"],
            ["impact_paths.id", "impact_paths.organization_id"],
            name="fk_impact_path_steps_path_tenant",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["entity_id", "organization_id"],
            ["entities.id", "entities.organization_id"],
            name="fk_impact_path_steps_entity_tenant",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["dependency_id", "organization_id"],
            ["dependencies.id", "dependencies.organization_id"],
            name="fk_impact_path_steps_dependency_tenant",
            ondelete="RESTRICT",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    path_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    sequence_index: Mapped[int] = mapped_column(Integer, nullable=False)
    entity_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    dependency_id: Mapped[UUID | None] = mapped_column(Uuid)


class ImpactResult(TimestampMixin, Base):
    __tablename__ = "impact_results"
    __table_args__ = (
        UniqueConstraint("id", "organization_id", name="uq_impact_results_id_organization"),
        UniqueConstraint(
            "organization_id", "run_id", "entity_id", name="uq_impact_results_run_entity"
        ),
        CheckConstraint("depth >= 0", name="ck_impact_results_depth_nonnegative"),
        CheckConstraint("score >= 0 AND score <= 100", name="ck_impact_results_score_range"),
        CheckConstraint(
            "confidence_value >= 0 AND confidence_value <= 1",
            name="ck_impact_results_confidence_range",
        ),
        Index(
            "ix_impact_results_organization_run_score",
            "organization_id",
            "run_id",
            "score",
        ),
        ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_impact_results_organization",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["run_id", "organization_id"],
            ["impact_runs.id", "impact_runs.organization_id"],
            name="fk_impact_results_run_tenant",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["entity_id", "organization_id"],
            ["entities.id", "entities.organization_id"],
            name="fk_impact_results_entity_tenant",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["primary_path_id", "organization_id", "run_id", "entity_id"],
            [
                "impact_paths.id",
                "impact_paths.organization_id",
                "impact_paths.run_id",
                "impact_paths.entity_id",
            ],
            name="fk_impact_results_primary_path_tenant",
            ondelete="RESTRICT",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    run_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    entity_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    depth: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[float] = mapped_column(nullable=False)
    confidence_value: Mapped[float] = mapped_column(nullable=False)
    confidence_label: Mapped[str] = mapped_column(String(40), nullable=False)
    primary_path_id: Mapped[UUID | None] = mapped_column(Uuid)
    explanation: Mapped[str] = mapped_column(Text, nullable=False, default="")
    result_flags: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)


class ScenarioEvent(Base):
    __tablename__ = "scenario_events"
    __table_args__ = (
        UniqueConstraint("organization_id", "scenario_id", name="uq_scenario_events_scenario"),
        ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_scenario_events_organization",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["scenario_id", "organization_id"],
            ["scenarios.id", "scenarios.organization_id"],
            name="fk_scenario_events_scenario_tenant",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["event_id", "organization_id"],
            ["events.id", "events.organization_id"],
            name="fk_scenario_events_event_tenant",
            ondelete="RESTRICT",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    scenario_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    event_id: Mapped[UUID | None] = mapped_column(Uuid)
    event_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ScenarioEntityOverride(Base):
    __tablename__ = "scenario_entity_overrides"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "scenario_id",
            "entity_id",
            name="uq_scenario_entity_overrides_target",
        ),
        CheckConstraint(
            "exposure IS NULL OR (exposure >= 0 AND exposure <= 1)",
            name="ck_scenario_entity_overrides_exposure_range",
        ),
        CheckConstraint(
            "mitigation IS NULL OR (mitigation >= 0 AND mitigation <= 1)",
            name="ck_scenario_entity_overrides_mitigation_range",
        ),
        CheckConstraint(
            "status IS NULL OR status IN ('active', 'inactive', 'archived')",
            name="ck_scenario_entity_overrides_status",
        ),
        ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_scenario_entity_overrides_organization",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["scenario_id", "organization_id"],
            ["scenarios.id", "scenarios.organization_id"],
            name="fk_scenario_entity_overrides_scenario_tenant",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["entity_id", "organization_id"],
            ["entities.id", "entities.organization_id"],
            name="fk_scenario_entity_overrides_entity_tenant",
            ondelete="RESTRICT",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    scenario_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    entity_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    exposure: Mapped[float | None] = mapped_column()
    mitigation: Mapped[float | None] = mapped_column()
    status: Mapped[str | None] = mapped_column(String(20))
    rationale: Mapped[str | None] = mapped_column(Text)


class ScenarioDependencyOverride(Base):
    __tablename__ = "scenario_dependency_overrides"
    __table_args__ = (
        CheckConstraint(
            "source_entity_id IS NULL OR target_entity_id IS NULL "
            "OR source_entity_id <> target_entity_id",
            name="ck_scenario_dependency_overrides_not_self",
        ),
        CheckConstraint(
            "weight IS NULL OR (weight >= 0 AND weight <= 1)",
            name="ck_scenario_dependency_overrides_weight_range",
        ),
        CheckConstraint(
            "dependency_id IS NOT NULL OR "
            "(source_entity_id IS NOT NULL AND target_entity_id IS NOT NULL)",
            name="ck_scenario_dependency_overrides_has_target",
        ),
        CheckConstraint(
            "review_status IS NULL OR review_status IN ('draft', 'reviewed', 'validated')",
            name="ck_scenario_dependency_overrides_review_status",
        ),
        CheckConstraint(
            "dependency_id IS NOT NULL OR "
            "(length(trim(relationship_type)) > 0 AND "
            "length(trim(relationship_label)) > 0)",
            name="ck_scenario_dependency_overrides_hypothetical_label",
        ),
        ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_scenario_dependency_overrides_organization",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["scenario_id", "organization_id"],
            ["scenarios.id", "scenarios.organization_id"],
            name="fk_scenario_dependency_overrides_scenario_tenant",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["dependency_id", "organization_id"],
            ["dependencies.id", "dependencies.organization_id"],
            name="fk_scenario_dependency_overrides_dependency_tenant",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["source_entity_id", "organization_id"],
            ["entities.id", "entities.organization_id"],
            name="fk_scenario_dependency_overrides_source_tenant",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["target_entity_id", "organization_id"],
            ["entities.id", "entities.organization_id"],
            name="fk_scenario_dependency_overrides_target_tenant",
            ondelete="RESTRICT",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    scenario_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    dependency_id: Mapped[UUID | None] = mapped_column(Uuid)
    source_entity_id: Mapped[UUID | None] = mapped_column(Uuid)
    target_entity_id: Mapped[UUID | None] = mapped_column(Uuid)
    relationship_type: Mapped[str | None] = mapped_column(String(60))
    relationship_label: Mapped[str | None] = mapped_column(String(80))
    weight: Mapped[float | None] = mapped_column()
    is_active: Mapped[bool | None] = mapped_column(Boolean)
    review_status: Mapped[str | None] = mapped_column(String(20))
    rationale: Mapped[str | None] = mapped_column(Text)


class Intervention(TimestampMixin, Base):
    __tablename__ = "interventions"
    __table_args__ = (
        CheckConstraint(
            "action_type IN ('mitigation', 'weight_override', "
            "'deactivate_dependency', 'hypothetical_dependency')",
            name="ck_interventions_action_type",
        ),
        CheckConstraint(
            "(target_entity_id IS NOT NULL AND target_dependency_id IS NULL) OR "
            "(target_entity_id IS NULL AND target_dependency_id IS NOT NULL)",
            name="ck_interventions_single_target",
        ),
        ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_interventions_organization",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["scenario_id", "organization_id"],
            ["scenarios.id", "scenarios.organization_id"],
            name="fk_interventions_scenario_tenant",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["author_user_id"],
            ["users.id"],
            name="fk_interventions_author",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["target_entity_id", "organization_id"],
            ["entities.id", "entities.organization_id"],
            name="fk_interventions_entity_tenant",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["target_dependency_id", "organization_id"],
            ["dependencies.id", "dependencies.organization_id"],
            name="fk_interventions_dependency_tenant",
            ondelete="RESTRICT",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    scenario_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    action_type: Mapped[str] = mapped_column(String(40), nullable=False)
    target_entity_id: Mapped[UUID | None] = mapped_column(Uuid)
    target_dependency_id: Mapped[UUID | None] = mapped_column(Uuid)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    assumptions: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    author_user_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_organization_created", "organization_id", "created_at"),
        Index(
            "ix_audit_logs_organization_resource",
            "organization_id",
            "resource_type",
            "resource_id",
        ),
        ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_audit_logs_organization",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["actor_user_id"],
            ["users.id"],
            name="fk_audit_logs_actor",
            ondelete="RESTRICT",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    actor_user_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(60), nullable=False)
    resource_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    request_id: Mapped[str | None] = mapped_column(String(128))
    summary: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
