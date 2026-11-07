from __future__ import annotations

import hashlib
import json
import math
from collections import deque
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from typing import Literal, TypeGuard
from uuid import UUID

import networkx as nx

ALGORITHM_VERSION = "ripple-engine-v1"
MAX_DEPTH = 10
MAX_PATHS_PER_TRIGGER = 10_000
MAX_NODES_PER_RUN = 5_000
REVIEW_CONFIDENCE: dict[str, tuple[float, str]] = {
    "draft": (0.5, "low"),
    "reviewed": (0.8, "medium"),
    "validated": (1.0, "high"),
}
IMPACT_THRESHOLDS = {
    "low": {"minimum": 0.0, "maximum": 25.0},
    "moderate": {"minimum": 25.0, "maximum": 50.0},
    "high": {"minimum": 50.0, "maximum": 75.0},
    "critical": {"minimum": 75.0, "maximum": 100.0},
}


class EngineInputError(ValueError):
    pass


@dataclass(frozen=True)
class EntitySnapshot:
    id: UUID
    organization_id: UUID
    name: str
    entity_type: str
    exposure: float = 1.0
    mitigation: float = 0.0
    status: str = "active"


@dataclass(frozen=True)
class DependencySnapshot:
    id: UUID
    organization_id: UUID
    source_entity_id: UUID
    target_entity_id: UUID
    relationship_type: str
    relationship_label: str
    weight: float
    review_status: str
    rationale: str | None = None
    is_active: bool = True
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    is_hypothetical: bool = False


@dataclass(frozen=True)
class EventTriggerSnapshot:
    entity_id: UUID
    exposure: float = 1.0
    rationale: str | None = None


@dataclass(frozen=True)
class AnalysisInput:
    organization_id: UUID
    event_id: UUID
    event_title: str
    event_status: str
    event_severity: int
    event_start_at: datetime
    triggers: tuple[EventTriggerSnapshot, ...]
    entities: tuple[EntitySnapshot, ...]
    dependencies: tuple[DependencySnapshot, ...]
    as_of: datetime | None = None
    max_depth: int = 4
    min_edge_weight: float = 0.0
    depth_attenuation: float = 0.8
    aggregation: Literal["max", "capped_sum"] = "max"
    max_paths_per_trigger: int = MAX_PATHS_PER_TRIGGER
    max_nodes_per_run: int = MAX_NODES_PER_RUN
    include_trigger_entities: bool = True
    algorithm_version: str = ALGORITHM_VERSION


@dataclass(frozen=True)
class PathStep:
    entity_id: UUID
    entity_name: str
    entity_type: str
    mitigation: float
    dependency_id: UUID | None
    relationship_type: str | None
    relationship_label: str | None
    weight: float | None
    review_status: str | None
    rationale: str | None
    is_hypothetical: bool


@dataclass(frozen=True)
class ImpactPath:
    trigger_entity_id: UUID
    entity_ids: tuple[UUID, ...]
    dependency_ids: tuple[UUID, ...]
    entity_names: tuple[str, ...]
    dependency_labels: tuple[str, ...]
    dependency_types: tuple[str, ...]
    weights: tuple[float, ...]
    review_statuses: tuple[str, ...]
    edge_count: int
    score: float
    confidence_value: float
    confidence_label: str
    weakest_review_status: str | None
    trigger_exposure: float
    trigger_mitigation: float
    event_severity: int
    steps: tuple[PathStep, ...]


@dataclass(frozen=True)
class TriggerEntityImpact:
    entity_id: UUID
    score: float
    impact_level: str
    depth: int
    path: ImpactPath


@dataclass(frozen=True)
class TriggerImpact:
    trigger_entity_id: UUID
    paths_enumerated: int
    results: tuple[TriggerEntityImpact, ...]


@dataclass(frozen=True)
class EntityImpact:
    entity_id: UUID
    entity_name: str
    entity_type: str
    depth: int
    score: float
    impact_level: str
    confidence_value: float
    confidence_label: str
    confidence_reason: str
    trigger_entity_ids: tuple[UUID, ...]
    primary_path: ImpactPath
    retained_paths: tuple[ImpactPath, ...]
    explanation: str


@dataclass(frozen=True)
class SafetyLimit:
    code: str
    configured_limit: int
    observed: int
    omitted: int | None
    trigger_entity_id: UUID | None = None


@dataclass(frozen=True)
class AnalysisCounts:
    eligible_nodes: int
    eligible_edges: int
    visited_nodes: int
    enumerated_paths: int


@dataclass(frozen=True)
class AnalysisOutput:
    status: Literal["completed", "completed_with_limits"]
    algorithm_version: str
    input_hash: str
    input_snapshot: dict[str, object]
    configuration: dict[str, object]
    trigger_results: tuple[TriggerImpact, ...]
    results: tuple[EntityImpact, ...]
    counts: AnalysisCounts
    limits: tuple[SafetyLimit, ...]
    warning: str | None


@dataclass(frozen=True)
class PreparedAnalysis:
    as_of: datetime
    configuration: dict[str, object]
    input_snapshot: dict[str, object]
    input_hash: str


def _snapshot_mapping(value: object, field: str) -> dict[str, object]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise EngineInputError(f"Snapshot field {field} must be an object.")
    return value


def _snapshot_list(value: object, field: str) -> list[object]:
    if not isinstance(value, list):
        raise EngineInputError(f"Snapshot field {field} must be an array.")
    return value


def _snapshot_value(mapping: dict[str, object], field: str) -> object:
    if field not in mapping:
        raise EngineInputError(f"Snapshot is missing field {field}.")
    return mapping[field]


def _snapshot_string(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise EngineInputError(f"Snapshot field {field} must be a string.")
    return value


def _snapshot_optional_string(value: object, field: str) -> str | None:
    if value is not None and not isinstance(value, str):
        raise EngineInputError(f"Snapshot field {field} must be a string or null.")
    return value


def _snapshot_number(value: object, field: str) -> float:
    if not _is_number(value) or not math.isfinite(value):
        raise EngineInputError(f"Snapshot field {field} must be a finite number.")
    return float(value)


def _snapshot_integer(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise EngineInputError(f"Snapshot field {field} must be an integer.")
    return value


def _snapshot_boolean(value: object, field: str) -> bool:
    if not isinstance(value, bool):
        raise EngineInputError(f"Snapshot field {field} must be a boolean.")
    return value


def _snapshot_uuid(value: object, field: str) -> UUID:
    raw = _snapshot_string(value, field)
    try:
        return UUID(raw)
    except ValueError as error:
        raise EngineInputError(f"Snapshot field {field} must be a UUID.") from error


def _snapshot_datetime(value: object, field: str) -> datetime:
    raw = _snapshot_string(value, field)
    try:
        return datetime.fromisoformat(raw)
    except ValueError as error:
        raise EngineInputError(f"Snapshot field {field} must be an ISO datetime.") from error


def _snapshot_aggregation(value: object) -> Literal["max", "capped_sum"]:
    aggregation = _snapshot_string(value, "configuration.aggregation")
    if aggregation == "max":
        return "max"
    if aggregation == "capped_sum":
        return "capped_sum"
    raise EngineInputError("Snapshot configuration has an unsupported aggregation.")


def analysis_input_from_snapshot(snapshot: dict[str, object]) -> AnalysisInput:
    event = _snapshot_mapping(_snapshot_value(snapshot, "event"), "event")
    configuration = _snapshot_mapping(
        _snapshot_value(snapshot, "configuration"),
        "configuration",
    )
    aggregation = _snapshot_aggregation(_snapshot_value(configuration, "aggregation"))

    triggers = tuple(
        EventTriggerSnapshot(
            entity_id=_snapshot_uuid(_snapshot_value(item, "entity_id"), "triggers.entity_id"),
            exposure=_snapshot_number(_snapshot_value(item, "exposure"), "triggers.exposure"),
            rationale=_snapshot_optional_string(
                _snapshot_value(item, "rationale"),
                "triggers.rationale",
            ),
        )
        for item in (
            _snapshot_mapping(value, "triggers[]")
            for value in _snapshot_list(_snapshot_value(snapshot, "triggers"), "triggers")
        )
    )
    entities = tuple(
        EntitySnapshot(
            id=_snapshot_uuid(_snapshot_value(item, "id"), "entities.id"),
            organization_id=_snapshot_uuid(
                _snapshot_value(item, "organization_id"),
                "entities.organization_id",
            ),
            name=_snapshot_string(_snapshot_value(item, "name"), "entities.name"),
            entity_type=_snapshot_string(
                _snapshot_value(item, "entity_type"),
                "entities.entity_type",
            ),
            exposure=_snapshot_number(_snapshot_value(item, "exposure"), "entities.exposure"),
            mitigation=_snapshot_number(
                _snapshot_value(item, "mitigation"),
                "entities.mitigation",
            ),
            status=_snapshot_string(_snapshot_value(item, "status"), "entities.status"),
        )
        for item in (
            _snapshot_mapping(value, "entities[]")
            for value in _snapshot_list(_snapshot_value(snapshot, "entities"), "entities")
        )
    )

    dependencies: list[DependencySnapshot] = []
    for value in _snapshot_list(_snapshot_value(snapshot, "dependencies"), "dependencies"):
        item = _snapshot_mapping(value, "dependencies[]")
        valid_from_value = _snapshot_value(item, "valid_from")
        valid_until_value = _snapshot_value(item, "valid_until")
        dependencies.append(
            DependencySnapshot(
                id=_snapshot_uuid(_snapshot_value(item, "id"), "dependencies.id"),
                organization_id=_snapshot_uuid(
                    _snapshot_value(item, "organization_id"),
                    "dependencies.organization_id",
                ),
                source_entity_id=_snapshot_uuid(
                    _snapshot_value(item, "source_entity_id"),
                    "dependencies.source_entity_id",
                ),
                target_entity_id=_snapshot_uuid(
                    _snapshot_value(item, "target_entity_id"),
                    "dependencies.target_entity_id",
                ),
                relationship_type=_snapshot_string(
                    _snapshot_value(item, "relationship_type"),
                    "dependencies.relationship_type",
                ),
                relationship_label=_snapshot_string(
                    _snapshot_value(item, "relationship_label"),
                    "dependencies.relationship_label",
                ),
                weight=_snapshot_number(_snapshot_value(item, "weight"), "dependencies.weight"),
                review_status=_snapshot_string(
                    _snapshot_value(item, "review_status"),
                    "dependencies.review_status",
                ),
                rationale=_snapshot_optional_string(
                    _snapshot_value(item, "rationale"),
                    "dependencies.rationale",
                ),
                is_active=_snapshot_boolean(
                    _snapshot_value(item, "is_active"),
                    "dependencies.is_active",
                ),
                valid_from=(
                    _snapshot_datetime(valid_from_value, "dependencies.valid_from")
                    if valid_from_value is not None
                    else None
                ),
                valid_until=(
                    _snapshot_datetime(valid_until_value, "dependencies.valid_until")
                    if valid_until_value is not None
                    else None
                ),
                is_hypothetical=_snapshot_boolean(
                    _snapshot_value(item, "is_hypothetical"),
                    "dependencies.is_hypothetical",
                ),
            )
        )

    return AnalysisInput(
        organization_id=_snapshot_uuid(
            _snapshot_value(snapshot, "organization_id"),
            "organization_id",
        ),
        event_id=_snapshot_uuid(_snapshot_value(event, "id"), "event.id"),
        event_title=_snapshot_string(_snapshot_value(event, "title"), "event.title"),
        event_status=_snapshot_string(_snapshot_value(event, "status"), "event.status"),
        event_severity=_snapshot_integer(
            _snapshot_value(event, "severity"),
            "event.severity",
        ),
        event_start_at=_snapshot_datetime(
            _snapshot_value(event, "start_at"),
            "event.start_at",
        ),
        triggers=triggers,
        entities=entities,
        dependencies=tuple(dependencies),
        as_of=_snapshot_datetime(
            _snapshot_value(configuration, "as_of"),
            "configuration.as_of",
        ),
        max_depth=_snapshot_integer(
            _snapshot_value(configuration, "max_depth"),
            "configuration.max_depth",
        ),
        min_edge_weight=_snapshot_number(
            _snapshot_value(configuration, "min_edge_weight"),
            "configuration.min_edge_weight",
        ),
        depth_attenuation=_snapshot_number(
            _snapshot_value(configuration, "depth_attenuation"),
            "configuration.depth_attenuation",
        ),
        aggregation=aggregation,
        max_paths_per_trigger=_snapshot_integer(
            _snapshot_value(configuration, "max_paths_per_trigger"),
            "configuration.max_paths_per_trigger",
        ),
        max_nodes_per_run=_snapshot_integer(
            _snapshot_value(configuration, "max_nodes_per_run"),
            "configuration.max_nodes_per_run",
        ),
        include_trigger_entities=_snapshot_boolean(
            _snapshot_value(configuration, "include_trigger_entities"),
            "configuration.include_trigger_entities",
        ),
        algorithm_version=_snapshot_string(
            _snapshot_value(snapshot, "algorithm_version"),
            "algorithm_version",
        ),
    )


def _is_number(value: object) -> TypeGuard[int | float]:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _validate_unit_interval(value: object, field: str) -> None:
    if not _is_number(value) or not math.isfinite(value) or not 0 <= value <= 1:
        raise EngineInputError(f"{field} must be a finite number between 0 and 1.")


def _validate_datetime(value: datetime | None, field: str) -> None:
    if value is not None and (
        not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None
    ):
        raise EngineInputError(f"{field} must include a timezone.")


def _utc(value: datetime) -> datetime:
    return value.astimezone(UTC)


def _validate_input(analysis: AnalysisInput) -> datetime:
    if not isinstance(analysis.organization_id, UUID) or not isinstance(analysis.event_id, UUID):
        raise EngineInputError("Organization and event IDs must be UUIDs.")
    if not isinstance(analysis.event_title, str) or not analysis.event_title.strip():
        raise EngineInputError("Event title must not be empty.")
    if analysis.event_status != "open":
        raise EngineInputError("Only open events can be run as live analyses.")
    if isinstance(analysis.event_severity, bool) or not isinstance(analysis.event_severity, int):
        raise EngineInputError("Event severity must be an integer between 0 and 100.")
    if not 0 <= analysis.event_severity <= 100:
        raise EngineInputError("Event severity must be an integer between 0 and 100.")
    _validate_datetime(analysis.event_start_at, "event_start_at")
    as_of = analysis.as_of or analysis.event_start_at
    _validate_datetime(as_of, "as_of")
    as_of = _utc(as_of)

    if (
        isinstance(analysis.max_depth, bool)
        or not isinstance(analysis.max_depth, int)
        or not 1 <= analysis.max_depth <= MAX_DEPTH
    ):
        raise EngineInputError(f"max_depth must be between 1 and {MAX_DEPTH}.")
    _validate_unit_interval(analysis.min_edge_weight, "min_edge_weight")
    _validate_unit_interval(analysis.depth_attenuation, "depth_attenuation")
    if not isinstance(analysis.aggregation, str) or analysis.aggregation not in {
        "max",
        "capped_sum",
    }:
        raise EngineInputError("aggregation must be 'max' or 'capped_sum'.")
    if (
        isinstance(analysis.max_paths_per_trigger, bool)
        or not isinstance(analysis.max_paths_per_trigger, int)
        or not 1 <= analysis.max_paths_per_trigger <= MAX_PATHS_PER_TRIGGER
    ):
        raise EngineInputError(
            f"max_paths_per_trigger must be between 1 and {MAX_PATHS_PER_TRIGGER}."
        )
    if (
        isinstance(analysis.max_nodes_per_run, bool)
        or not isinstance(analysis.max_nodes_per_run, int)
        or not 1 <= analysis.max_nodes_per_run <= MAX_NODES_PER_RUN
    ):
        raise EngineInputError(f"max_nodes_per_run must be between 1 and {MAX_NODES_PER_RUN}.")
    if not isinstance(analysis.include_trigger_entities, bool):
        raise EngineInputError("include_trigger_entities must be a boolean.")
    if (
        not isinstance(analysis.algorithm_version, str)
        or not analysis.algorithm_version
        or len(analysis.algorithm_version) > 80
    ):
        raise EngineInputError("algorithm_version must contain 1 to 80 characters.")

    if not analysis.triggers:
        raise EngineInputError("At least one event trigger is required.")
    if len(analysis.triggers) > analysis.max_nodes_per_run:
        raise EngineInputError("max_nodes_per_run cannot be lower than the number of triggers.")

    entity_by_id: dict[UUID, EntitySnapshot] = {}
    for item in analysis.entities:
        if not isinstance(item.id, UUID):
            raise EngineInputError("Entity IDs must be UUIDs.")
        if item.id in entity_by_id:
            raise EngineInputError("Duplicate entity ID.")
        if (
            not isinstance(item.organization_id, UUID)
            or item.organization_id != analysis.organization_id
        ):
            raise EngineInputError("All entities must belong to the run organization.")
        if not isinstance(item.status, str) or item.status not in {
            "active",
            "inactive",
            "archived",
        }:
            raise EngineInputError("Entity status is not supported.")
        if (
            not isinstance(item.name, str)
            or not item.name.strip()
            or not isinstance(item.entity_type, str)
            or not item.entity_type.strip()
        ):
            raise EngineInputError("Entity name and type must not be empty.")
        _validate_unit_interval(item.exposure, "entity exposure")
        _validate_unit_interval(item.mitigation, "entity mitigation")
        entity_by_id[item.id] = item

    trigger_ids: set[UUID] = set()
    for item in analysis.triggers:
        if not isinstance(item.entity_id, UUID):
            raise EngineInputError("Trigger entity IDs must be UUIDs.")
        if item.entity_id in trigger_ids:
            raise EngineInputError("Duplicate trigger entity ID.")
        _validate_unit_interval(item.exposure, "trigger exposure")
        entity = entity_by_id.get(item.entity_id)
        if entity is None:
            raise EngineInputError(
                "Every trigger must reference an entity in the run organization."
            )
        if entity.status == "archived":
            raise EngineInputError("A trigger cannot reference an archived entity.")
        trigger_ids.add(item.entity_id)

    dependency_ids: set[UUID] = set()
    ordered_pairs: set[tuple[UUID, UUID]] = set()
    for edge in analysis.dependencies:
        if not isinstance(edge.id, UUID):
            raise EngineInputError("Dependency IDs must be UUIDs.")
        if edge.id in dependency_ids:
            raise EngineInputError("Duplicate dependency ID.")
        dependency_ids.add(edge.id)
        if (
            not isinstance(edge.organization_id, UUID)
            or edge.organization_id != analysis.organization_id
        ):
            raise EngineInputError("All dependencies must belong to the run organization.")
        if not isinstance(edge.source_entity_id, UUID) or not isinstance(
            edge.target_entity_id, UUID
        ):
            raise EngineInputError("Dependency endpoints must be UUIDs.")
        if edge.source_entity_id == edge.target_entity_id:
            raise EngineInputError("Dependencies cannot contain a self-loop.")
        pair = (edge.source_entity_id, edge.target_entity_id)
        if pair in ordered_pairs:
            raise EngineInputError("Duplicate ordered pair of dependencies is not allowed.")
        ordered_pairs.add(pair)
        if edge.source_entity_id not in entity_by_id or edge.target_entity_id not in entity_by_id:
            raise EngineInputError("Every dependency endpoint must reference a run entity.")
        _validate_unit_interval(edge.weight, "dependency weight")
        if not isinstance(edge.review_status, str) or edge.review_status not in REVIEW_CONFIDENCE:
            raise EngineInputError("Dependency review status is not supported.")
        if (
            not isinstance(edge.relationship_type, str)
            or not edge.relationship_type.strip()
            or not isinstance(edge.relationship_label, str)
            or not edge.relationship_label.strip()
        ):
            raise EngineInputError("Dependency type and label must not be empty.")
        _validate_datetime(edge.valid_from, "dependency valid_from")
        _validate_datetime(edge.valid_until, "dependency valid_until")
        if (
            edge.valid_from is not None
            and edge.valid_until is not None
            and _utc(edge.valid_until) <= _utc(edge.valid_from)
        ):
            raise EngineInputError("Dependency valid_until must be later than valid_from.")
        if not isinstance(edge.is_active, bool) or not isinstance(edge.is_hypothetical, bool):
            raise EngineInputError("Dependency activity and hypothetical flags must be booleans.")

    return as_of


def _configuration(analysis: AnalysisInput, as_of: datetime) -> dict[str, object]:
    return {
        "as_of": as_of.isoformat(),
        "max_depth": analysis.max_depth,
        "min_edge_weight": float(analysis.min_edge_weight),
        "depth_attenuation": float(analysis.depth_attenuation),
        "aggregation": analysis.aggregation,
        "max_paths_per_trigger": analysis.max_paths_per_trigger,
        "max_nodes_per_run": analysis.max_nodes_per_run,
        "include_trigger_entities": analysis.include_trigger_entities,
        "impact_thresholds": {level: dict(bounds) for level, bounds in IMPACT_THRESHOLDS.items()},
    }


def _canonical_snapshot(
    analysis: AnalysisInput,
    as_of: datetime,
    configuration: dict[str, object],
) -> dict[str, object]:
    return {
        "algorithm_version": analysis.algorithm_version,
        "organization_id": str(analysis.organization_id),
        "event": {
            "id": str(analysis.event_id),
            "title": analysis.event_title,
            "status": analysis.event_status,
            "severity": analysis.event_severity,
            "start_at": _utc(analysis.event_start_at).isoformat(),
        },
        "triggers": [
            {
                "entity_id": str(item.entity_id),
                "exposure": float(item.exposure),
                "rationale": item.rationale,
            }
            for item in sorted(analysis.triggers, key=lambda value: str(value.entity_id))
        ],
        "entities": [
            {
                "id": str(item.id),
                "organization_id": str(item.organization_id),
                "name": item.name,
                "entity_type": item.entity_type,
                "exposure": float(item.exposure),
                "mitigation": float(item.mitigation),
                "status": item.status,
            }
            for item in sorted(analysis.entities, key=lambda value: str(value.id))
        ],
        "dependencies": [
            {
                "id": str(item.id),
                "organization_id": str(item.organization_id),
                "source_entity_id": str(item.source_entity_id),
                "target_entity_id": str(item.target_entity_id),
                "relationship_type": item.relationship_type,
                "relationship_label": item.relationship_label,
                "weight": float(item.weight),
                "review_status": item.review_status,
                "rationale": item.rationale,
                "is_active": item.is_active,
                "valid_from": _utc(item.valid_from).isoformat()
                if item.valid_from is not None
                else None,
                "valid_until": _utc(item.valid_until).isoformat()
                if item.valid_until is not None
                else None,
                "is_hypothetical": item.is_hypothetical,
            }
            for item in sorted(analysis.dependencies, key=lambda value: str(value.id))
        ],
        "configuration": {**configuration, "as_of": as_of.isoformat()},
    }


def _confidence(statuses: tuple[str, ...]) -> tuple[float, str, str | None]:
    if not statuses:
        return 1.0, "high", None
    weakest = min(statuses, key=lambda item: REVIEW_CONFIDENCE[item][0])
    value, label = REVIEW_CONFIDENCE[weakest]
    return value, label, weakest


def _path_sort_key(path: ImpactPath) -> tuple[object, ...]:
    return (
        -path.score,
        path.edge_count,
        tuple(str(item) for item in path.entity_ids),
        tuple(str(item) for item in path.dependency_ids),
        str(path.trigger_entity_id),
    )


def _impact_level(score: float) -> str:
    if score < 25:
        return "low"
    if score < 50:
        return "moderate"
    if score < 75:
        return "high"
    return "critical"


def _path_output(
    analysis: AnalysisInput,
    trigger_item: EventTriggerSnapshot,
    entity_ids: tuple[UUID, ...],
    dependencies: tuple[DependencySnapshot, ...],
    entities: dict[UUID, EntitySnapshot],
    score: float,
) -> ImpactPath:
    statuses = tuple(
        "draft" if edge.is_hypothetical else edge.review_status for edge in dependencies
    )
    confidence_value, confidence_label, weakest = _confidence(statuses)
    trigger_entity = entities[trigger_item.entity_id]
    steps = [
        PathStep(
            entity_id=trigger_entity.id,
            entity_name=trigger_entity.name,
            entity_type=trigger_entity.entity_type,
            mitigation=trigger_entity.mitigation,
            dependency_id=None,
            relationship_type=None,
            relationship_label=None,
            weight=None,
            review_status=None,
            rationale=None,
            is_hypothetical=False,
        )
    ]
    for entity_id, edge in zip(entity_ids[1:], dependencies, strict=True):
        entered_entity = entities[entity_id]
        steps.append(
            PathStep(
                entity_id=entered_entity.id,
                entity_name=entered_entity.name,
                entity_type=entered_entity.entity_type,
                mitigation=entered_entity.mitigation,
                dependency_id=edge.id,
                relationship_type=edge.relationship_type,
                relationship_label=edge.relationship_label,
                weight=edge.weight,
                review_status="draft" if edge.is_hypothetical else edge.review_status,
                rationale=edge.rationale,
                is_hypothetical=edge.is_hypothetical,
            )
        )
    return ImpactPath(
        trigger_entity_id=trigger_item.entity_id,
        entity_ids=entity_ids,
        dependency_ids=tuple(edge.id for edge in dependencies),
        entity_names=tuple(entities[item].name for item in entity_ids),
        dependency_labels=tuple(edge.relationship_label for edge in dependencies),
        dependency_types=tuple(edge.relationship_type for edge in dependencies),
        weights=tuple(edge.weight for edge in dependencies),
        review_statuses=statuses,
        edge_count=len(dependencies),
        score=score,
        confidence_value=confidence_value,
        confidence_label=confidence_label,
        weakest_review_status=weakest,
        trigger_exposure=trigger_item.exposure,
        trigger_mitigation=trigger_entity.mitigation,
        event_severity=analysis.event_severity,
        steps=tuple(steps),
    )


def _eligible_graph(
    analysis: AnalysisInput,
    as_of: datetime,
) -> tuple[nx.DiGraph, dict[UUID, EntitySnapshot], tuple[DependencySnapshot, ...]]:
    entities = {item.id: item for item in analysis.entities if item.status != "archived"}
    graph = nx.DiGraph()
    graph.add_nodes_from((entity_id, {"snapshot": item}) for entity_id, item in entities.items())
    eligible_dependencies = tuple(
        sorted(
            (
                edge
                for edge in analysis.dependencies
                if edge.is_active
                and edge.weight >= analysis.min_edge_weight
                and edge.source_entity_id in entities
                and edge.target_entity_id in entities
                and (edge.valid_from is None or _utc(edge.valid_from) <= as_of)
                and (edge.valid_until is None or as_of < _utc(edge.valid_until))
            ),
            key=lambda item: (str(item.source_entity_id), str(item.target_entity_id), str(item.id)),
        )
    )
    for edge in eligible_dependencies:
        graph.add_edge(edge.source_entity_id, edge.target_entity_id, snapshot=edge)
    return graph, entities, eligible_dependencies


def _limited_nodes(
    graph: nx.DiGraph,
    trigger_ids: tuple[UUID, ...],
    maximum: int,
) -> tuple[set[UUID], bool]:
    selected: set[UUID] = set()
    queue = deque(trigger_ids)
    while queue and len(selected) < maximum:
        node = queue.popleft()
        if node in selected:
            continue
        selected.add(node)
        for target in sorted(graph.successors(node), key=str):
            if target not in selected:
                queue.append(target)

    omitted_reachable = any(node not in selected for node in queue)
    if len(selected) < maximum:
        for node in sorted(set(graph.nodes) - selected, key=str):
            if len(selected) == maximum:
                break
            selected.add(node)
    return selected, len(graph.nodes) > maximum or omitted_reachable


def _minimum_depths(graph: nx.DiGraph, trigger_ids: tuple[UUID, ...]) -> dict[UUID, int]:
    depths = {trigger_id: 0 for trigger_id in trigger_ids}
    queue = deque(trigger_ids)
    while queue:
        current = queue.popleft()
        for target in sorted(graph.successors(current), key=str):
            if target not in depths:
                depths[target] = depths[current] + 1
                queue.append(target)
    return depths


def _enumerate_paths(
    analysis: AnalysisInput,
    trigger_item: EventTriggerSnapshot,
    graph: nx.DiGraph,
    entities: dict[UUID, EntitySnapshot],
) -> tuple[list[ImpactPath], int, bool]:
    trigger_entity = entities[trigger_item.entity_id]
    initial_score = (
        analysis.event_severity
        / 100
        * trigger_item.exposure
        * (1 - trigger_entity.mitigation)
        * 100
    )
    paths: list[ImpactPath] = []
    path_limit_reached = False

    def visit(
        entity_ids: tuple[UUID, ...],
        dependencies: tuple[DependencySnapshot, ...],
        score: float,
    ) -> bool:
        nonlocal path_limit_reached
        if len(paths) >= analysis.max_paths_per_trigger:
            path_limit_reached = True
            return True
        paths.append(
            _path_output(analysis, trigger_item, entity_ids, dependencies, entities, score)
        )
        if len(dependencies) >= analysis.max_depth:
            return False

        current = entity_ids[-1]
        for target in sorted(graph.successors(current), key=str):
            if target in entity_ids:
                continue
            edge = graph.edges[current, target]["snapshot"]
            next_score = (
                score * edge.weight * analysis.depth_attenuation * (1 - entities[target].mitigation)
            )
            if visit(entity_ids + (target,), dependencies + (edge,), next_score):
                return True
        return False

    visit((trigger_item.entity_id,), (), initial_score)
    return paths, len(paths), path_limit_reached


def _explanation(
    analysis: AnalysisInput,
    result: EntityImpact,
    warning: str | None,
) -> str:
    primary = result.primary_path
    path_text = primary.entity_names[0]
    for label, weight, name in zip(
        primary.dependency_labels,
        primary.weights,
        primary.entity_names[1:],
        strict=True,
    ):
        path_text += f" -[{label}, weight {weight:g}]-> {name}"
    depth_note = (
        f" The minimum depth is {result.depth}, while the primary path has "
        f"{primary.edge_count} edges."
        if result.depth != primary.edge_count
        else f" The minimum depth and primary-path length are {result.depth}."
    )
    edge_reviews = ", ".join(primary.review_statuses) or "no dependencies"
    trigger_names = ", ".join(
        f"{next(item.name for item in analysis.entities if item.id == trigger_id)} ({trigger_id})"
        for trigger_id in result.trigger_entity_ids
    )
    mitigation_assumptions = ", ".join(
        f"{step.entity_name}={step.mitigation:g}" for step in primary.steps
    )
    aggregation_note = (
        " The score combines distinct incoming dependency paths and is capped at 100."
        if analysis.aggregation == "capped_sum"
        else " The score uses the highest-scoring qualifying simple path."
    )
    return (
        f"{result.entity_name} is connected from trigger(s) "
        f"{trigger_names} by {path_text}. "
        f"The primary path has {primary.edge_count} edges; event severity is "
        f"{analysis.event_severity}/100, trigger exposure is {primary.trigger_exposure:g}, "
        f"and trigger mitigation is {primary.trigger_mitigation:g}. Node mitigations along "
        f"the primary path are {mitigation_assumptions}. Depth attenuation is "
        f"{analysis.depth_attenuation:g}.{depth_note} The weakest dependency review "
        f"status on the primary path is {primary.weakest_review_status or 'none'} "
        f"({edge_reviews}). Confidence is {primary.confidence_label} and describes "
        "dependency review quality, not the likelihood of an outcome."
        f"{aggregation_note} The aggregate estimated score is {result.score:.1f}/100."
        f"{' ' + warning if warning else ''}"
    )


def prepare_analysis_input(analysis: AnalysisInput) -> PreparedAnalysis:
    as_of = _validate_input(analysis)
    configuration = _configuration(analysis, as_of)
    snapshot = _canonical_snapshot(analysis, as_of, configuration)
    canonical = json.dumps(snapshot, sort_keys=True, separators=(",", ":"), allow_nan=False)
    input_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return PreparedAnalysis(
        as_of=as_of,
        configuration=configuration,
        input_snapshot=snapshot,
        input_hash=input_hash,
    )


def run_analysis(analysis: AnalysisInput) -> AnalysisOutput:
    prepared = prepare_analysis_input(analysis)
    configuration = prepared.configuration
    snapshot = prepared.input_snapshot
    input_hash = prepared.input_hash
    as_of = prepared.as_of
    full_graph, full_entities, eligible_dependencies = _eligible_graph(analysis, as_of)
    trigger_ids = tuple(sorted((item.entity_id for item in analysis.triggers), key=str))
    selected_nodes, node_limit_reached = _limited_nodes(
        full_graph,
        trigger_ids,
        analysis.max_nodes_per_run,
    )
    graph = full_graph.subgraph(selected_nodes).copy()
    entity_by_id = {entity_id: full_entities[entity_id] for entity_id in selected_nodes}
    depths = _minimum_depths(graph, trigger_ids)

    limits: list[SafetyLimit] = []
    if node_limit_reached:
        limits.append(
            SafetyLimit(
                code="max_nodes_per_run",
                configured_limit=analysis.max_nodes_per_run,
                observed=full_graph.number_of_nodes(),
                omitted=full_graph.number_of_nodes() - len(selected_nodes),
            )
        )

    trigger_paths: dict[UUID, list[ImpactPath]] = {}
    path_counts: dict[UUID, int] = {}
    for trigger_item in sorted(analysis.triggers, key=lambda item: str(item.entity_id)):
        paths, count, path_limit_reached = _enumerate_paths(
            analysis,
            trigger_item,
            graph,
            entity_by_id,
        )
        trigger_paths[trigger_item.entity_id] = paths
        path_counts[trigger_item.entity_id] = count
        if path_limit_reached:
            limits.append(
                SafetyLimit(
                    code="max_paths_per_trigger",
                    configured_limit=analysis.max_paths_per_trigger,
                    observed=count,
                    omitted=None,
                    trigger_entity_id=trigger_item.entity_id,
                )
            )

    unique_paths: dict[tuple[tuple[UUID, ...], tuple[UUID, ...]], ImpactPath] = {}
    for paths in trigger_paths.values():
        for path in paths:
            unique_paths.setdefault((path.entity_ids, path.dependency_ids), path)

    paths_by_entity: dict[UUID, list[ImpactPath]] = {}
    for path in unique_paths.values():
        paths_by_entity.setdefault(path.entity_ids[-1], []).append(path)

    trigger_set = set(trigger_ids)
    impact_results: list[EntityImpact] = []
    trigger_entity_results: dict[UUID, list[TriggerEntityImpact]] = {
        trigger_id: [] for trigger_id in trigger_ids
    }
    for trigger_id, paths in trigger_paths.items():
        per_entity: dict[UUID, list[ImpactPath]] = {}
        for path in paths:
            per_entity.setdefault(path.entity_ids[-1], []).append(path)
        for entity_id, candidates in per_entity.items():
            path = min(candidates, key=_path_sort_key)
            trigger_entity_results[trigger_id].append(
                TriggerEntityImpact(
                    entity_id=entity_id,
                    score=path.score,
                    impact_level=_impact_level(path.score),
                    depth=depths[entity_id],
                    path=path,
                )
            )

    for entity_id in sorted(paths_by_entity, key=str):
        if not analysis.include_trigger_entities and entity_id in trigger_set:
            continue
        candidates = paths_by_entity[entity_id]
        if analysis.aggregation == "max":
            retained = tuple(sorted(candidates, key=_path_sort_key))
        else:
            best_by_final_edge: dict[tuple[str, UUID], ImpactPath] = {}
            for path in candidates:
                final_edge_key = (
                    ("edge", path.dependency_ids[-1])
                    if path.dependency_ids
                    else ("trigger", path.trigger_entity_id)
                )
                current = best_by_final_edge.get(final_edge_key)
                if current is None or _path_sort_key(path) < _path_sort_key(current):
                    best_by_final_edge[final_edge_key] = path
            retained = tuple(sorted(best_by_final_edge.values(), key=_path_sort_key))

        primary = min(retained, key=_path_sort_key)
        score = (
            primary.score
            if analysis.aggregation == "max"
            else min(100.0, sum(path.score for path in retained))
        )
        entity = entity_by_id[entity_id]
        contributing_triggers = tuple(
            sorted({path.trigger_entity_id for path in retained}, key=str)
        )
        impact = EntityImpact(
            entity_id=entity_id,
            entity_name=entity.name,
            entity_type=entity.entity_type,
            depth=depths[entity_id],
            score=score,
            impact_level=_impact_level(score),
            confidence_value=primary.confidence_value,
            confidence_label=primary.confidence_label,
            confidence_reason=(
                f"The weakest review status is {primary.weakest_review_status or 'none'}; "
                "confidence describes dependency review quality, not the likelihood of an outcome."
            ),
            trigger_entity_ids=contributing_triggers,
            primary_path=primary,
            retained_paths=retained,
            explanation="",
        )
        impact_results.append(impact)

    # Construct explanations after each result's final aggregate value is fixed.
    results: list[EntityImpact] = []
    for item in impact_results:
        result = item
        results.append(
            replace(
                result,
                explanation=_explanation(
                    analysis,
                    result,
                    warning="Run is potentially incomplete. "
                    + " ".join(
                        f"{limit.code} reached at {limit.configured_limit}." for limit in limits
                    )
                    if limits
                    else None,
                ),
            )
        )

    trigger_results = tuple(
        TriggerImpact(
            trigger_entity_id=trigger_id,
            paths_enumerated=path_counts[trigger_id],
            results=tuple(
                sorted(
                    trigger_entity_results[trigger_id],
                    key=lambda item: str(item.entity_id),
                )
            ),
        )
        for trigger_id in trigger_ids
    )
    warnings = []
    for item in limits:
        omitted = (
            f"{item.omitted} omitted"
            if item.omitted is not None
            else "additional candidates omitted (count not enumerated)"
        )
        warnings.append(
            f"{item.code} limit reached: {item.observed} observed, {omitted} "
            f"at configured ceiling {item.configured_limit}."
        )
    return AnalysisOutput(
        status="completed_with_limits" if limits else "completed",
        algorithm_version=analysis.algorithm_version,
        input_hash=input_hash,
        input_snapshot=snapshot,
        configuration=configuration,
        trigger_results=trigger_results,
        results=tuple(results),
        counts=AnalysisCounts(
            eligible_nodes=full_graph.number_of_nodes(),
            eligible_edges=len(eligible_dependencies),
            visited_nodes=len(selected_nodes),
            enumerated_paths=sum(path_counts.values()),
        ),
        limits=tuple(limits),
        warning="Run is potentially incomplete. " + " ".join(warnings) if warnings else None,
    )
