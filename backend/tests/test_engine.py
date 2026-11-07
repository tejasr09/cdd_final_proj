from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import Literal
from uuid import UUID

import pytest

from app.engine import (
    ALGORITHM_VERSION,
    AnalysisInput,
    DependencySnapshot,
    EngineInputError,
    EntitySnapshot,
    EventTriggerSnapshot,
    analysis_input_from_snapshot,
    run_analysis,
)

ORG_ID = UUID(int=1)
OTHER_ORG_ID = UUID(int=2)
EVENT_ID = UUID(int=100)
AS_OF = datetime(2026, 11, 7, 12, 0, tzinfo=UTC)


def uid(value: int) -> UUID:
    return UUID(int=value)


def entity(
    entity_id: int,
    *,
    name: str | None = None,
    mitigation: float = 0.0,
    status: str = "active",
    organization_id: UUID = ORG_ID,
) -> EntitySnapshot:
    return EntitySnapshot(
        id=uid(entity_id),
        organization_id=organization_id,
        name=name or f"Entity {entity_id}",
        entity_type="resource",
        exposure=1.0,
        mitigation=mitigation,
        status=status,
    )


def dependency(
    dependency_id: int,
    source: int,
    target: int,
    weight: float,
    *,
    review_status: str = "validated",
    is_active: bool = True,
    valid_from: datetime | None = None,
    valid_until: datetime | None = None,
    is_hypothetical: bool = False,
    organization_id: UUID = ORG_ID,
) -> DependencySnapshot:
    return DependencySnapshot(
        id=uid(dependency_id),
        organization_id=organization_id,
        source_entity_id=uid(source),
        target_entity_id=uid(target),
        relationship_type="affects",
        relationship_label=f"edge {dependency_id}",
        weight=weight,
        review_status=review_status,
        rationale=None,
        is_active=is_active,
        valid_from=valid_from,
        valid_until=valid_until,
        is_hypothetical=is_hypothetical,
    )


def trigger(entity_id: int, exposure: float = 1.0) -> EventTriggerSnapshot:
    return EventTriggerSnapshot(entity_id=uid(entity_id), exposure=exposure)


def make_input(
    *,
    entities: tuple[EntitySnapshot, ...] | None = None,
    dependencies: tuple[DependencySnapshot, ...] = (),
    triggers: tuple[EventTriggerSnapshot, ...] = (trigger(10),),
    severity: int = 100,
    event_status: str = "open",
    as_of: datetime | None = AS_OF,
    max_depth: int = 4,
    min_edge_weight: float = 0.0,
    depth_attenuation: float = 0.8,
    aggregation: Literal["max", "capped_sum"] = "max",
    max_paths_per_trigger: int = 10_000,
    max_nodes_per_run: int = 5_000,
    include_trigger_entities: bool = True,
) -> AnalysisInput:
    if entities is None:
        ids = {item.entity_id.int for item in triggers}
        ids.update(edge.source_entity_id.int for edge in dependencies)
        ids.update(edge.target_entity_id.int for edge in dependencies)
        entities = tuple(entity(entity_id) for entity_id in sorted(ids))
    return AnalysisInput(
        organization_id=ORG_ID,
        event_id=EVENT_ID,
        event_title="Synthetic test event",
        event_status=event_status,
        event_severity=severity,
        event_start_at=AS_OF,
        triggers=triggers,
        entities=entities,
        dependencies=dependencies,
        as_of=as_of,
        max_depth=max_depth,
        min_edge_weight=min_edge_weight,
        depth_attenuation=depth_attenuation,
        aggregation=aggregation,
        max_paths_per_trigger=max_paths_per_trigger,
        max_nodes_per_run=max_nodes_per_run,
        include_trigger_entities=include_trigger_entities,
    )


def result_for(output, entity_id: int):
    return next(result for result in output.results if result.entity_id == uid(entity_id))


def test_trigger_only_score_includes_trigger_exposure_and_mitigation() -> None:
    analysis = make_input(
        entities=(entity(10, mitigation=0.2),),
        triggers=(trigger(10, exposure=0.5),),
        severity=90,
    )

    output = run_analysis(analysis)
    result = result_for(output, 10)

    assert result.depth == 0
    assert result.score == pytest.approx(36.0)
    assert result.primary_path.entity_ids == (uid(10),)
    assert result.primary_path.edge_count == 0
    assert result.confidence_value == 1.0
    assert result.confidence_label == "high"
    assert output.status == "completed"


def test_one_edge_applies_entered_node_mitigation_once() -> None:
    output = run_analysis(
        make_input(
            entities=(entity(10, mitigation=0.2), entity(11, mitigation=0.25)),
            dependencies=(dependency(20, 10, 11, 0.8),),
            triggers=(trigger(10, exposure=0.5),),
            severity=90,
        )
    )

    assert result_for(output, 11).score == pytest.approx(17.28)


def test_two_edge_synopsis_example_scores_32_256_and_displays_32_3() -> None:
    output = run_analysis(
        make_input(
            dependencies=(dependency(20, 10, 11, 0.8), dependency(21, 11, 12, 0.7)),
            severity=90,
            depth_attenuation=0.8,
        )
    )

    assert result_for(output, 12).score == pytest.approx(32.256)
    assert f"{result_for(output, 12).score:.1f}" == "32.3"


def test_stored_snapshot_reproduces_the_complete_analysis_output() -> None:
    analysis = make_input(
        dependencies=(
            dependency(20, 10, 11, 0.8, review_status="reviewed"),
            dependency(21, 11, 12, 0.7, review_status="validated"),
        ),
        aggregation="capped_sum",
    )

    original = run_analysis(analysis)
    replayed = run_analysis(analysis_input_from_snapshot(original.input_snapshot))

    assert replayed == original


def test_invalid_stored_snapshot_is_rejected() -> None:
    with pytest.raises(EngineInputError, match="missing field event"):
        analysis_input_from_snapshot({})


def test_edge_direction_is_source_to_target() -> None:
    output = run_analysis(make_input(dependencies=(dependency(20, 10, 11, 1.0),)))

    assert {result.entity_id for result in output.results} == {uid(10), uid(11)}


def test_reverse_edge_does_not_propagate_from_trigger() -> None:
    output = run_analysis(make_input(dependencies=(dependency(20, 11, 10, 1.0),)))

    assert {result.entity_id for result in output.results} == {uid(10)}


def test_disconnected_entities_are_not_impact_results() -> None:
    output = run_analysis(make_input(entities=(entity(10), entity(11), entity(12))))

    assert [result.entity_id for result in output.results] == [uid(10)]


def test_cycle_enumerates_only_simple_paths() -> None:
    output = run_analysis(
        make_input(
            dependencies=(
                dependency(20, 10, 11, 0.9),
                dependency(21, 11, 12, 0.9),
                dependency(22, 12, 11, 0.9),
            )
        )
    )

    paths = result_for(output, 12).retained_paths
    assert all(len(path.entity_ids) == len(set(path.entity_ids)) for path in paths)
    assert all(uid(10) not in path.entity_ids[1:] for path in paths)


def test_longer_path_can_be_primary_when_its_score_is_higher() -> None:
    output = run_analysis(
        make_input(
            dependencies=(
                dependency(20, 10, 12, 0.3),
                dependency(21, 10, 11, 0.9),
                dependency(22, 11, 12, 0.9),
            )
        )
    )
    result = result_for(output, 12)

    assert result.depth == 1
    assert result.primary_path.edge_count == 2
    assert result.score == pytest.approx(51.84)
    assert "minimum depth is 1" in result.explanation.lower()


def test_equal_scores_use_fewer_edges_then_lexicographic_entity_ids() -> None:
    short_and_long = run_analysis(
        make_input(
            dependencies=(
                dependency(20, 10, 12, 0.8),
                dependency(21, 10, 11, 0.8),
                dependency(22, 11, 12, 1.0),
            ),
            depth_attenuation=1.0,
        )
    )
    assert result_for(short_and_long, 12).primary_path.edge_count == 1

    tied = run_analysis(
        make_input(
            dependencies=(
                dependency(21, 10, 11, 0.8),
                dependency(22, 11, 13, 1.0),
                dependency(23, 10, 12, 0.8),
                dependency(24, 12, 13, 1.0),
            ),
            depth_attenuation=1.0,
        )
    )
    assert result_for(tied, 13).primary_path.entity_ids == (uid(10), uid(11), uid(13))


def test_max_aggregation_selects_highest_scoring_path() -> None:
    output = run_analysis(
        make_input(
            dependencies=(
                dependency(20, 10, 11, 0.5),
                dependency(21, 10, 12, 0.9),
                dependency(22, 11, 13, 0.5),
                dependency(23, 12, 13, 0.8),
            )
        )
    )
    result = result_for(output, 13)

    assert result.score == pytest.approx(46.08)
    assert result.primary_path.entity_ids == (uid(10), uid(12), uid(13))
    assert len(result.retained_paths) == 2


def test_capped_sum_uses_best_path_per_distinct_final_edge_once() -> None:
    output = run_analysis(
        make_input(
            dependencies=(
                dependency(20, 10, 11, 1.0),
                dependency(21, 11, 14, 0.5),
                dependency(22, 10, 12, 1.0),
                dependency(23, 12, 14, 0.4),
                dependency(24, 10, 13, 0.9),
                dependency(25, 13, 11, 0.9),
            ),
            depth_attenuation=1.0,
            aggregation="capped_sum",
        )
    )
    result = result_for(output, 14)

    assert result.score == pytest.approx(90.0)
    assert {path.dependency_ids[-1] for path in result.retained_paths} == {uid(21), uid(23)}
    assert len(result.retained_paths) == 2
    assert "capped at 100" in result.explanation


def test_capped_sum_is_capped_at_100() -> None:
    output = run_analysis(
        make_input(
            dependencies=(
                dependency(20, 10, 11, 1.0),
                dependency(21, 11, 13, 0.8),
                dependency(22, 10, 12, 1.0),
                dependency(23, 12, 13, 0.8),
            ),
            depth_attenuation=1.0,
            aggregation="capped_sum",
        )
    )

    assert result_for(output, 13).score == 100.0


def test_multiple_triggers_are_aggregated_without_losing_provenance() -> None:
    output = run_analysis(
        make_input(
            entities=(entity(10), entity(11), entity(12)),
            dependencies=(dependency(20, 10, 12, 0.5), dependency(21, 11, 12, 0.8)),
            triggers=(trigger(10), trigger(11)),
        )
    )
    result = result_for(output, 12)

    assert result.score == pytest.approx(64.0)
    assert result.primary_path.trigger_entity_id == uid(11)
    assert set(result.trigger_entity_ids) == {uid(10), uid(11)}
    assert len(output.trigger_results) == 2


def test_duplicate_trigger_entities_are_rejected() -> None:
    with pytest.raises(EngineInputError, match="(?i)duplicate trigger"):
        run_analysis(make_input(triggers=(trigger(10), trigger(10, 0.5))))


@pytest.mark.parametrize(
    ("review_status", "expected_value", "expected_label"),
    [
        ("draft", 0.5, "low"),
        ("reviewed", 0.8, "medium"),
        ("validated", 1.0, "high"),
    ],
)
def test_confidence_uses_weakest_review_status(
    review_status: str,
    expected_value: float,
    expected_label: str,
) -> None:
    output = run_analysis(
        make_input(
            dependencies=(
                dependency(20, 10, 11, 1.0, review_status="validated"),
                dependency(21, 11, 12, 1.0, review_status=review_status),
            ),
            depth_attenuation=1.0,
        )
    )
    result = result_for(output, 12)

    assert result.confidence_value == expected_value
    assert result.confidence_label == expected_label
    assert "not the likelihood" in result.confidence_reason


def test_hypothetical_scenario_dependency_counts_as_draft_confidence() -> None:
    output = run_analysis(
        make_input(
            dependencies=(
                dependency(20, 10, 11, 0.9, review_status="validated", is_hypothetical=True),
            )
        )
    )

    result = result_for(output, 11)
    assert result.confidence_value == 0.5
    assert result.confidence_label == "low"


def test_inactive_dependency_is_not_eligible() -> None:
    output = run_analysis(make_input(dependencies=(dependency(20, 10, 11, 1.0, is_active=False),)))

    assert {result.entity_id for result in output.results} == {uid(10)}
    assert output.counts.eligible_edges == 0


def test_dependency_validity_window_is_start_inclusive_end_exclusive() -> None:
    output = run_analysis(
        make_input(
            dependencies=(
                dependency(
                    20,
                    10,
                    11,
                    0.8,
                    valid_from=AS_OF,
                    valid_until=AS_OF + timedelta(seconds=1),
                ),
                dependency(
                    21,
                    10,
                    12,
                    0.8,
                    valid_from=AS_OF - timedelta(seconds=1),
                    valid_until=AS_OF,
                ),
            )
        )
    )

    assert uid(11) in {result.entity_id for result in output.results}
    assert uid(12) not in {result.entity_id for result in output.results}


def test_archived_dependency_endpoint_is_excluded() -> None:
    output = run_analysis(
        make_input(
            entities=(entity(10), entity(11, status="archived")),
            dependencies=(dependency(20, 10, 11, 1.0),),
        )
    )

    assert {result.entity_id for result in output.results} == {uid(10)}
    assert output.counts.eligible_edges == 0


def test_minimum_edge_weight_boundary_is_inclusive() -> None:
    output = run_analysis(
        make_input(
            dependencies=(dependency(20, 10, 11, 0.5), dependency(21, 10, 12, 0.499999)),
            min_edge_weight=0.5,
        )
    )

    assert uid(11) in {result.entity_id for result in output.results}
    assert uid(12) not in {result.entity_id for result in output.results}
    assert output.counts.eligible_edges == 1


def test_maximum_depth_boundary_is_inclusive() -> None:
    output = run_analysis(
        make_input(
            dependencies=(dependency(20, 10, 11, 1.0), dependency(21, 11, 12, 1.0)),
            max_depth=1,
        )
    )

    assert uid(11) in {result.entity_id for result in output.results}
    assert uid(12) not in {result.entity_id for result in output.results}


@pytest.mark.parametrize(
    ("score", "expected_level"),
    [
        (24.999999, "low"),
        (25.0, "moderate"),
        (49.999999, "moderate"),
        (50.0, "high"),
        (74.999999, "high"),
        (75.0, "critical"),
    ],
)
def test_impact_level_thresholds(score: float, expected_level: str) -> None:
    output = run_analysis(
        make_input(
            entities=(entity(10),),
            triggers=(trigger(10, exposure=score / 100),),
        )
    )

    assert result_for(output, 10).impact_level == expected_level


def test_path_ceiling_returns_explicit_incomplete_status_and_details() -> None:
    output = run_analysis(
        make_input(
            dependencies=(
                dependency(20, 10, 11, 1.0),
                dependency(21, 10, 12, 1.0),
            ),
            max_paths_per_trigger=2,
        )
    )

    assert output.status == "completed_with_limits"
    assert output.counts.enumerated_paths == 2
    assert any(limit.code == "max_paths_per_trigger" for limit in output.limits)
    assert output.warning and "incomplete" in output.warning.lower()


def test_node_ceiling_returns_explicit_incomplete_status_and_details() -> None:
    output = run_analysis(
        make_input(
            entities=(entity(10), entity(11), entity(12)),
            dependencies=(dependency(20, 10, 11, 1.0), dependency(21, 11, 12, 1.0)),
            max_nodes_per_run=2,
        )
    )

    assert output.status == "completed_with_limits"
    assert output.counts.eligible_nodes == 3
    assert output.counts.visited_nodes == 2
    assert any(limit.code == "max_nodes_per_run" for limit in output.limits)
    assert uid(12) not in {result.entity_id for result in output.results}


def test_identical_inputs_have_deterministic_hash_and_results() -> None:
    dependencies = (dependency(20, 10, 11, 0.7), dependency(21, 10, 12, 0.8))
    first = run_analysis(make_input(dependencies=dependencies))
    reordered = run_analysis(
        make_input(
            dependencies=tuple(reversed(dependencies)),
            entities=tuple(reversed(make_input(dependencies=dependencies).entities)),
        )
    )

    assert first.input_hash == reordered.input_hash
    assert first.results == reordered.results
    assert first.input_snapshot == reordered.input_snapshot
    assert first.algorithm_version == ALGORITHM_VERSION


def test_changed_input_changes_canonical_hash() -> None:
    first = run_analysis(make_input(severity=80))
    second = run_analysis(make_input(severity=81))

    assert first.input_hash != second.input_hash


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("weight", float("nan")),
        ("weight", -0.01),
        ("weight", 1.01),
        ("severity", -1),
        ("severity", 101),
        ("mitigation", -0.01),
        ("mitigation", 1.01),
    ],
)
def test_invalid_numeric_inputs_are_rejected(field: str, value: float) -> None:
    if field == "weight":
        analysis = make_input(dependencies=(dependency(20, 10, 11, value),))
    elif field == "severity":
        analysis = make_input(severity=int(value))
    else:
        analysis = make_input(entities=(entity(10, mitigation=value),))

    with pytest.raises(EngineInputError):
        run_analysis(analysis)


def test_invalid_organization_reference_and_self_loop_are_rejected() -> None:
    cross_tenant = make_input(
        dependencies=(dependency(20, 10, 11, 1.0, organization_id=OTHER_ORG_ID),)
    )
    self_loop = make_input(dependencies=(dependency(20, 10, 10, 1.0),))

    with pytest.raises(EngineInputError, match="organization"):
        run_analysis(cross_tenant)
    with pytest.raises(EngineInputError, match="self-loop"):
        run_analysis(self_loop)


def test_duplicate_dependency_ids_and_ordered_pairs_are_rejected() -> None:
    repeated_id = make_input(
        dependencies=(dependency(20, 10, 11, 0.5), dependency(20, 11, 12, 0.5))
    )
    repeated_pair = make_input(
        dependencies=(dependency(20, 10, 11, 0.5), dependency(21, 10, 11, 0.8))
    )

    with pytest.raises(EngineInputError, match="(?i)duplicate dependency ID"):
        run_analysis(repeated_id)
    with pytest.raises(EngineInputError, match="(?i)duplicate ordered pair"):
        run_analysis(repeated_pair)


def test_event_status_must_be_open_and_missing_trigger_is_rejected() -> None:
    with pytest.raises(EngineInputError, match="open"):
        run_analysis(make_input(event_status="draft"))
    with pytest.raises(EngineInputError, match="trigger"):
        run_analysis(make_input(entities=(entity(11),), triggers=(trigger(10),)))


def test_empty_dependency_graph_and_trigger_display_option() -> None:
    only_trigger = run_analysis(make_input(dependencies=()))
    hidden_trigger = run_analysis(
        make_input(dependencies=(dependency(20, 10, 11, 0.8),), include_trigger_entities=False)
    )

    assert [result.entity_id for result in only_trigger.results] == [uid(10)]
    assert [result.entity_id for result in hidden_trigger.results] == [uid(11)]


def test_zero_depth_attenuation_keeps_downstream_paths_with_zero_scores() -> None:
    output = run_analysis(
        make_input(
            dependencies=(dependency(20, 10, 11, 1.0),),
            depth_attenuation=0.0,
        )
    )

    assert result_for(output, 11).score == 0.0
    assert result_for(output, 11).primary_path.edge_count == 1


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("max_depth", 0),
        ("max_depth", 11),
        ("max_paths_per_trigger", 0),
        ("max_paths_per_trigger", 10_001),
        ("max_nodes_per_run", 0),
        ("max_nodes_per_run", 5_001),
        ("min_edge_weight", 1.01),
        ("depth_attenuation", -0.01),
        ("aggregation", "average"),
    ],
)
def test_invalid_configuration_is_rejected(field: str, value: object) -> None:
    with pytest.raises(EngineInputError):
        run_analysis(replace(make_input(), **{field: value}))


def test_explicit_as_of_overrides_event_start_default() -> None:
    analysis = make_input(as_of=None)
    output = run_analysis(analysis)
    assert output.configuration["as_of"] == AS_OF.isoformat()


def test_all_path_identifiers_are_unique_when_trigger_paths_overlap() -> None:
    output = run_analysis(
        make_input(
            entities=(entity(10), entity(11), entity(12)),
            dependencies=(dependency(20, 10, 12, 0.8), dependency(21, 11, 12, 0.8)),
            triggers=(trigger(10), trigger(11)),
        )
    )
    path_ids = {
        (path.entity_ids, path.dependency_ids)
        for result in output.results
        for path in result.retained_paths
    }

    assert len(path_ids) == sum(len(result.retained_paths) for result in output.results)


def test_input_snapshot_is_immutable_and_contains_effective_configuration() -> None:
    analysis = make_input(dependencies=(dependency(20, 10, 11, 0.8),))
    output = run_analysis(analysis)
    event_snapshot = output.input_snapshot["event"]
    configuration_snapshot = output.input_snapshot["configuration"]
    dependency_snapshots = output.input_snapshot["dependencies"]

    assert isinstance(event_snapshot, dict)
    assert isinstance(configuration_snapshot, dict)
    assert isinstance(dependency_snapshots, list)
    assert event_snapshot["id"] == str(EVENT_ID)
    assert configuration_snapshot["aggregation"] == "max"
    assert dependency_snapshots[0]["weight"] == 0.8
    assert output.configuration["impact_thresholds"] == {
        "low": {"minimum": 0.0, "maximum": 25.0},
        "moderate": {"minimum": 25.0, "maximum": 50.0},
        "high": {"minimum": 50.0, "maximum": 75.0},
        "critical": {"minimum": 75.0, "maximum": 100.0},
    }


def test_invalid_duplicate_entity_ids_are_rejected() -> None:
    with pytest.raises(EngineInputError, match="(?i)duplicate entity ID"):
        run_analysis(make_input(entities=(entity(10), entity(10))))
