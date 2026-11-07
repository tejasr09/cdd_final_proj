from datetime import UTC, datetime
from typing import Annotated, Generic, Literal, TypeVar
from uuid import UUID

from pydantic import (
    AfterValidator,
    AwareDatetime,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    model_validator,
)

EntityType = Literal["person", "department", "resource", "activity", "system", "location", "group"]
EntityStatus = Literal["active", "inactive", "archived"]
EventStatus = Literal["draft", "open", "resolved", "archived"]
ReviewStatus = Literal["draft", "reviewed", "validated"]


def _normalize_utc(value: object) -> object:
    if not isinstance(value, datetime):
        return value
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


UTCDateTime = Annotated[
    AwareDatetime, BeforeValidator(_normalize_utc), AfterValidator(_normalize_utc)
]


class RequestModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ORMResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class EntityCreate(RequestModel):
    name: str = Field(min_length=1, max_length=160)
    entity_type: EntityType
    description: str | None = Field(default=None, max_length=5000)
    exposure: float = Field(default=1.0, ge=0, le=1)
    mitigation: float = Field(default=0.0, ge=0, le=1)
    attributes: dict[str, object] = Field(default_factory=dict)


class EntityUpdate(RequestModel):
    expected_updated_at: UTCDateTime
    name: str | None = Field(default=None, min_length=1, max_length=160)
    entity_type: EntityType | None = None
    description: str | None = Field(default=None, max_length=5000)
    exposure: float | None = Field(default=None, ge=0, le=1)
    mitigation: float | None = Field(default=None, ge=0, le=1)
    attributes: dict[str, object] | None = None

    @model_validator(mode="after")
    def require_changes(self) -> "EntityUpdate":
        if self.model_fields_set <= {"expected_updated_at"}:
            raise ValueError("At least one entity field must be provided.")
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError(
                "Null values are not accepted in entity updates; omit unchanged fields."
            )
        return self


class EntityResponse(ORMResponse):
    id: UUID
    name: str
    description: str | None
    entity_type: EntityType
    status: EntityStatus
    exposure: float
    mitigation: float
    attributes: dict[str, object]
    archived_at: UTCDateTime | None
    created_at: UTCDateTime
    updated_at: UTCDateTime


class DependencyCreate(RequestModel):
    source_entity_id: UUID
    target_entity_id: UUID
    relationship_type: str = Field(min_length=1, max_length=60)
    relationship_label: str | None = Field(default=None, min_length=1, max_length=80)
    weight: float = Field(ge=0, le=1)
    rationale: str | None = Field(default=None, max_length=5000)
    review_status: ReviewStatus = "draft"
    is_active: bool = True
    valid_from: UTCDateTime | None = None
    valid_until: UTCDateTime | None = None

    @model_validator(mode="after")
    def validate_dependency(self) -> "DependencyCreate":
        if self.source_entity_id == self.target_entity_id:
            raise ValueError("A dependency cannot reference the same source and target.")
        if self.valid_from and self.valid_until and self.valid_until <= self.valid_from:
            raise ValueError("valid_until must be later than valid_from.")
        return self


class DependencyUpdate(RequestModel):
    expected_updated_at: UTCDateTime
    source_entity_id: UUID | None = None
    target_entity_id: UUID | None = None
    relationship_type: str | None = Field(default=None, min_length=1, max_length=60)
    relationship_label: str | None = Field(default=None, min_length=1, max_length=80)
    weight: float | None = Field(default=None, ge=0, le=1)
    rationale: str | None = Field(default=None, max_length=5000)
    review_status: ReviewStatus | None = None
    valid_from: UTCDateTime | None = None
    valid_until: UTCDateTime | None = None

    @model_validator(mode="after")
    def require_changes(self) -> "DependencyUpdate":
        if self.model_fields_set <= {"expected_updated_at"}:
            raise ValueError("At least one dependency field must be provided.")
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError(
                "Null values are not accepted in dependency updates; omit unchanged fields."
            )
        return self


class DependencyActivation(RequestModel):
    expected_updated_at: UTCDateTime
    is_active: bool


class DependencyResponse(ORMResponse):
    id: UUID
    source_entity_id: UUID
    target_entity_id: UUID
    relationship_type: str
    relationship_label: str
    weight: float
    rationale: str | None
    review_status: ReviewStatus
    is_active: bool
    valid_from: UTCDateTime | None
    valid_until: UTCDateTime | None
    created_at: UTCDateTime
    updated_at: UTCDateTime


class EventCreate(RequestModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    severity: int = Field(ge=0, le=100)
    start_at: UTCDateTime
    duration_minutes: int | None = Field(default=None, gt=0)
    status: Literal["draft", "open"] = "draft"


class EventUpdate(RequestModel):
    expected_updated_at: UTCDateTime
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    severity: int | None = Field(default=None, ge=0, le=100)
    start_at: UTCDateTime | None = None
    duration_minutes: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def require_changes(self) -> "EventUpdate":
        if self.model_fields_set <= {"expected_updated_at"}:
            raise ValueError("At least one event field must be provided.")
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError(
                "Null values are not accepted in event updates; omit unchanged fields."
            )
        return self


class EventStatusUpdate(RequestModel):
    expected_updated_at: UTCDateTime
    status: Literal["open", "resolved", "archived"]


class EventResponse(ORMResponse):
    id: UUID
    title: str
    description: str | None
    severity: int
    start_at: UTCDateTime
    duration_minutes: int | None
    status: EventStatus
    created_at: UTCDateTime
    updated_at: UTCDateTime


class EventTriggerCreate(RequestModel):
    entity_id: UUID
    exposure: float = Field(default=1.0, ge=0, le=1)
    rationale: str | None = Field(default=None, max_length=2000)


class EventTriggerResponse(ORMResponse):
    id: UUID
    event_id: UUID
    entity_id: UUID
    exposure: float
    rationale: str | None
    created_at: UTCDateTime


class AnalysisRunCreate(RequestModel):
    as_of: UTCDateTime | None = None
    max_depth: int = Field(default=4, ge=1, le=10)
    min_edge_weight: float = Field(default=0.0, ge=0, le=1, allow_inf_nan=False)
    depth_attenuation: float = Field(default=0.8, ge=0, le=1, allow_inf_nan=False)
    aggregation: Literal["max", "capped_sum"] = "max"
    max_paths_per_trigger: int = Field(default=10_000, ge=1, le=10_000)
    max_nodes_per_run: int = Field(default=5_000, ge=1, le=5_000)
    include_trigger_entities: bool = True


class ScenarioCreate(RequestModel):
    name: str = Field(min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=5000)
    baseline_run_id: UUID

    @model_validator(mode="after")
    def validate_name(self) -> "ScenarioCreate":
        if not self.name.strip():
            raise ValueError("Scenario name must not be empty.")
        return self


class ScenarioUpdate(RequestModel):
    expected_version: int = Field(ge=1)
    name: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=5000)

    @model_validator(mode="after")
    def require_changes(self) -> "ScenarioUpdate":
        if self.model_fields_set <= {"expected_version"}:
            raise ValueError("At least one scenario field must be provided.")
        if self.name is not None and not self.name.strip():
            raise ValueError("Scenario name must not be empty.")
        return self


class ScenarioEventUpdate(RequestModel):
    expected_version: int = Field(ge=1)
    title: str | None = Field(default=None, min_length=1, max_length=200)
    severity: int | None = Field(default=None, ge=0, le=100)
    start_at: UTCDateTime | None = None

    @model_validator(mode="after")
    def require_changes(self) -> "ScenarioEventUpdate":
        if self.model_fields_set <= {"expected_version"}:
            raise ValueError("At least one event overlay field must be provided.")
        if any(
            getattr(self, field) is None for field in self.model_fields_set - {"expected_version"}
        ):
            raise ValueError("Null values are not accepted in event overlays.")
        if self.title is not None and not self.title.strip():
            raise ValueError("Event title must not be empty.")
        return self


ScenarioInterventionType = Literal[
    "mitigation",
    "weight_override",
    "deactivate_dependency",
    "hypothetical_dependency",
]


class ScenarioInterventionCreate(RequestModel):
    expected_version: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=160)
    action_type: ScenarioInterventionType
    target_entity_id: UUID | None = None
    target_dependency_id: UUID | None = None
    source_entity_id: UUID | None = None
    mitigation: float | None = Field(default=None, ge=0, le=1, allow_inf_nan=False)
    weight: float | None = Field(default=None, ge=0, le=1, allow_inf_nan=False)
    relationship_type: str | None = Field(default=None, min_length=1, max_length=60)
    relationship_label: str | None = Field(default=None, min_length=1, max_length=80)
    rationale: str = Field(min_length=1, max_length=5000)
    assumptions: dict[str, object] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_action(self) -> "ScenarioInterventionCreate":
        if not self.title.strip() or not self.rationale.strip():
            raise ValueError("Intervention title and rationale must not be empty.")
        if self.relationship_type is not None and not self.relationship_type.strip():
            raise ValueError("Relationship type must not be empty.")
        if self.relationship_label is not None and not self.relationship_label.strip():
            raise ValueError("Relationship label must not be empty.")
        action_fields = {
            "mitigation": self.mitigation,
            "weight": self.weight,
            "relationship_type": self.relationship_type,
            "relationship_label": self.relationship_label,
            "source_entity_id": self.source_entity_id,
        }
        if self.action_type == "mitigation":
            valid = (
                self.target_entity_id is not None
                and self.target_dependency_id is None
                and self.mitigation is not None
                and all(
                    action_fields[field] is None
                    for field in (
                        "weight",
                        "relationship_type",
                        "relationship_label",
                        "source_entity_id",
                    )
                )
            )
        elif self.action_type == "weight_override":
            valid = (
                self.target_dependency_id is not None
                and self.target_entity_id is None
                and self.weight is not None
                and self.mitigation is None
                and self.relationship_type is None
                and self.relationship_label is None
                and self.source_entity_id is None
            )
        elif self.action_type == "deactivate_dependency":
            valid = (
                self.target_dependency_id is not None
                and self.target_entity_id is None
                and all(value is None for value in action_fields.values())
            )
        else:
            valid = (
                self.target_entity_id is not None
                and self.target_dependency_id is None
                and self.source_entity_id is not None
                and self.source_entity_id != self.target_entity_id
                and self.weight is not None
                and self.relationship_type is not None
                and self.relationship_label is not None
                and self.mitigation is None
            )
        if not valid:
            raise ValueError("Intervention fields do not match the selected action type.")
        return self


class ScenarioAnalysisRunCreate(RequestModel):
    expected_version: int = Field(ge=1)
    as_of: UTCDateTime | None = None
    max_depth: int | None = Field(default=None, ge=1, le=10)
    min_edge_weight: float | None = Field(default=None, ge=0, le=1, allow_inf_nan=False)
    depth_attenuation: float | None = Field(default=None, ge=0, le=1, allow_inf_nan=False)
    aggregation: Literal["max", "capped_sum"] | None = None
    max_paths_per_trigger: int | None = Field(default=None, ge=1, le=10_000)
    max_nodes_per_run: int | None = Field(default=None, ge=1, le=5_000)
    include_trigger_entities: bool | None = None


class ScenarioResponse(ORMResponse):
    id: UUID
    organization_id: UUID
    name: str
    description: str | None
    baseline_run_id: UUID | None
    status: Literal["draft", "archived"]
    version: int
    created_by_user_id: UUID
    created_at: UTCDateTime
    updated_at: UTCDateTime


class ScenarioEventResponse(BaseModel):
    event: dict[str, object]
    triggers: list[dict[str, object]]


class ScenarioEntityOverrideResponse(ORMResponse):
    id: UUID
    scenario_id: UUID
    entity_id: UUID
    exposure: float | None
    mitigation: float | None
    status: EntityStatus | None
    rationale: str | None


class ScenarioDependencyOverrideResponse(ORMResponse):
    id: UUID
    scenario_id: UUID
    dependency_id: UUID | None
    source_entity_id: UUID | None
    target_entity_id: UUID | None
    relationship_type: str | None
    relationship_label: str | None
    weight: float | None
    is_active: bool | None
    review_status: ReviewStatus | None
    rationale: str | None


class ScenarioInterventionResponse(ORMResponse):
    id: UUID
    scenario_id: UUID
    title: str
    action_type: ScenarioInterventionType
    target_entity_id: UUID | None
    target_dependency_id: UUID | None
    rationale: str
    assumptions: dict[str, object]
    author_user_id: UUID
    created_at: UTCDateTime


class ScenarioDetailResponse(ScenarioResponse):
    event_overlay: ScenarioEventResponse
    entity_overrides: list[ScenarioEntityOverrideResponse]
    dependency_overrides: list[ScenarioDependencyOverrideResponse]
    interventions: list[ScenarioInterventionResponse]


class ScenarioComparisonItem(BaseModel):
    entity_id: UUID
    entity_name: str
    change_type: Literal["added", "removed", "changed", "unchanged"]
    baseline_score: float
    scenario_score: float
    delta: float


class ScenarioComparisonResponse(BaseModel):
    scenario_id: UUID
    baseline_run_id: UUID
    scenario_run_id: UUID
    scenario_version: int
    baseline_status: Literal[
        "pending",
        "running",
        "completed",
        "completed_with_limits",
        "incomplete",
        "failed",
    ]
    scenario_status: Literal[
        "pending",
        "running",
        "completed",
        "completed_with_limits",
        "incomplete",
        "failed",
    ]
    potentially_incomplete: bool
    estimated_effect: dict[str, float]
    assumptions: list[ScenarioInterventionResponse]
    items: list[ScenarioComparisonItem]


AnalysisRunStatus = Literal[
    "pending",
    "running",
    "completed",
    "completed_with_limits",
    "incomplete",
    "failed",
]


class AnalysisRunResponse(ORMResponse):
    id: UUID
    organization_id: UUID
    event_id: UUID
    scenario_id: UUID | None
    status: AnalysisRunStatus
    configuration: dict[str, object]
    algorithm_version: str
    input_hash: str
    as_of: UTCDateTime
    summary: dict[str, object]
    created_by_user_id: UUID
    created_at: UTCDateTime
    updated_at: UTCDateTime


class ImpactResultResponse(ORMResponse):
    id: UUID
    run_id: UUID
    entity_id: UUID
    entity_name: str
    entity_type: EntityType
    depth: int
    score: float
    impact_level: Literal["low", "moderate", "high", "critical"]
    confidence_value: float
    confidence_label: Literal["low", "medium", "high"]
    confidence_reason: str
    primary_path_id: UUID | None
    trigger_entity_ids: list[UUID]
    explanation: str
    result_flags: dict[str, object]


class ImpactPathResponse(ORMResponse):
    id: UUID
    run_id: UUID
    entity_id: UUID
    trigger_entity_id: UUID
    score: float
    edge_count: int
    is_primary: bool
    provenance: dict[str, object]


T = TypeVar("T")


class PageResponse(BaseModel, Generic[T]):
    items: list[T]
    limit: int
    offset: int
    total: int


class ErrorDetail(BaseModel):
    field: str
    message: str
    code: str


class ErrorBody(BaseModel):
    code: str
    message: str
    details: list[ErrorDetail] = Field(default_factory=list)
    request_id: str


class ErrorEnvelope(BaseModel):
    error: ErrorBody
