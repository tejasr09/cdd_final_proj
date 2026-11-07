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
