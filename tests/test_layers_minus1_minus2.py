"""Tests for CIMF Layer -1 (Coherence & Identity) and Layer -2 (Meta-Governance).

Both layers were exercised only indirectly through the full-stack cycle, which
left roughly half of each file uncovered. These target their public APIs
directly.
"""

import dataclasses

import pytest

from cimf.layer_minus1 import (
    DEFAULT_LAMBDA_MIN,
    MEANING_ROT_THRESHOLD,
    CoherenceIdentityEngine,
    IdentityVector,
    ImmutableSemanticContainer,
    PlasticityBudget,
)
from cimf.layer_minus2 import (
    AttractorState,
    MetaGovernanceEngine,
    SpatialNode,
    merge_nodes,
)


# --- Layer -1: identity ------------------------------------------------------

def test_identity_distance_is_zero_for_identical_vectors():
    a = IdentityVector({"x": 0.5, "y": 0.25})
    b = IdentityVector({"x": 0.5, "y": 0.25})
    assert a.distance(b) == 0.0


def test_identity_distance_is_symmetric_and_handles_missing_keys():
    a = IdentityVector({"x": 1.0})
    b = IdentityVector({"y": 1.0})
    # missing keys are treated as 0.0, so this is sqrt((1+1)/2) == 1.0
    assert a.distance(b) == pytest.approx(1.0)
    assert a.distance(b) == pytest.approx(b.distance(a))


def test_empty_identity_vectors_have_zero_distance():
    assert IdentityVector({}).distance(IdentityVector({})) == 0.0


def test_plasticity_budget_decays_then_floors_at_minimum():
    budget = PlasticityBudget(initial=0.10, decay=0.005, minimum=DEFAULT_LAMBDA_MIN)
    first = budget.tick()
    assert first < 0.10
    for _ in range(500):
        budget.tick()
    assert budget.value == DEFAULT_LAMBDA_MIN
    assert budget.epoch == 501


def test_update_identity_before_initialisation_raises():
    engine = CoherenceIdentityEngine()
    with pytest.raises(RuntimeError):
        engine.update_identity(IdentityVector({"x": 0.1}))


def test_small_drift_is_accepted_and_bumps_version():
    engine = CoherenceIdentityEngine()
    engine.set_identity(IdentityVector({"x": 0.50}))
    assert engine.current_identity.version == 0

    accepted = engine.update_identity(IdentityVector({"x": 0.51}))
    assert accepted is True
    assert engine.current_identity.version == 1
    assert engine.mean_drift() > 0.0


def test_drift_beyond_plasticity_budget_is_rejected():
    engine = CoherenceIdentityEngine()
    engine.set_identity(IdentityVector({"x": 0.0}))
    # lambda starts at 0.10; a drift of 0.9 is far outside it
    assert engine.update_identity(IdentityVector({"x": 0.9})) is False
    # the rejected vector must not become the current identity
    assert engine.current_identity.features == {"x": 0.0}
    assert engine.current_identity.version == 0


def test_meaning_rot_detection_is_unreachable_under_the_default_budget():
    """KNOWN LIMITATION, pinned deliberately.

    MEANING_ROT_THRESHOLD is 0.30, but update_identity returns False for any
    drift greater than lambda(t), which starts at 0.10 and only decays. So the
    rot branch below it can never execute with default settings and
    meaning_rot_events stays at zero no matter how violent the drift.

    Raising lambda_initial above the threshold is what makes it reachable.
    """
    engine = CoherenceIdentityEngine()
    engine.set_identity(IdentityVector({"x": 0.0}))
    for step in range(1, 6):
        engine.update_identity(IdentityVector({"x": float(step)}))
    assert engine.fossilise()["meaning_rot_events"] == 0

    permissive = CoherenceIdentityEngine(lambda_initial=MEANING_ROT_THRESHOLD * 2)
    permissive.set_identity(IdentityVector({"x": 0.0}))
    assert permissive.update_identity(IdentityVector({"x": 0.4})) is True
    assert permissive.fossilise()["meaning_rot_events"] == 1


# --- Layer -1: immutable semantic containers ---------------------------------

def test_container_verifies_its_own_execution_proof():
    isc = ImmutableSemanticContainer.create("seed", {"k": 1}, "model-v1")
    assert isc.verify() is True


def test_container_verify_detects_a_tampered_delta():
    isc = ImmutableSemanticContainer.create("seed", {"k": 1}, "model-v1")
    tampered = dataclasses.replace(isc, delta={"k": 999})
    assert tampered.verify() is False


def test_isc_chain_links_parents_and_verifies_end_to_end():
    engine = CoherenceIdentityEngine()
    first = engine.package("seed-a", {"n": 1}, "model-v1")
    second = engine.package("seed-b", {"n": 2}, "model-v1")

    assert first.parent_id is None
    assert second.parent_id == first.container_id
    assert engine.verify_chain() is True


def test_fossilise_reports_chain_and_budget_state():
    engine = CoherenceIdentityEngine()
    engine.set_identity(IdentityVector({"x": 0.5}))
    engine.package("seed", {"n": 1}, "model-v1")
    engine.update_identity(IdentityVector({"x": 0.505}))

    fossil = engine.fossilise()
    assert fossil["isc_count"] == 1
    assert fossil["chain_valid"] is True
    assert fossil["identity_version"] == 1
    assert fossil["plasticity_epoch"] == 1


# --- Layer -2: attractor states and phi ---------------------------------------

def test_attractor_state_rejects_values_outside_the_unit_interval():
    with pytest.raises(ValueError):
        AttractorState(eta=1.5, A=0.5, G=0.5, C=0.5, R=0.5).validate()
    with pytest.raises(ValueError):
        AttractorState(eta=0.5, A=-0.1, G=0.5, C=0.5, R=0.5).validate()


def test_phi_is_the_weighted_sum_of_the_attractor_state():
    engine = MetaGovernanceEngine()  # default weights are 0.2 each
    result = engine.evaluate(AttractorState(eta=1.0, A=0.0, G=0.0, C=0.0, R=0.0))
    assert result.phi == pytest.approx(0.20)
    assert engine.phi_history == [pytest.approx(0.20)]


def test_weights_must_sum_to_one():
    with pytest.raises(ValueError):
        MetaGovernanceEngine(weights={"eta": 0.5, "A": 0.5, "G": 0.5, "C": 0.5, "R": 0.5})


def test_weights_must_use_the_expected_keys():
    with pytest.raises(ValueError):
        MetaGovernanceEngine(weights={"eta": 0.5, "A": 0.5})


def test_failed_rebalance_leaves_the_previous_weights_intact():
    engine = MetaGovernanceEngine()
    original = dict(engine.weights)
    with pytest.raises(ValueError):
        engine.rebalance_weights({"eta": 9.0, "A": 0.0, "G": 0.0, "C": 0.0, "R": 0.0})
    assert engine.weights == original


def test_successful_rebalance_changes_phi():
    engine = MetaGovernanceEngine()
    engine.rebalance_weights({"eta": 1.0, "A": 0.0, "G": 0.0, "C": 0.0, "R": 0.0})
    result = engine.evaluate(AttractorState(eta=0.5, A=1.0, G=1.0, C=1.0, R=1.0))
    assert result.phi == pytest.approx(0.5)


def test_phi_moving_average_is_none_before_any_evaluation():
    assert MetaGovernanceEngine().phi_moving_average() is None


# --- Layer -2: catatonia detection --------------------------------------------

def test_catatonia_is_unreachable_under_the_default_weights():
    """KNOWN LIMITATION, pinned deliberately.

    Catatonia requires phi >= 0.85 *and* G < 0.15 across the window. With the
    default weights of 0.20 each, the largest phi obtainable while G < 0.15 is
    0.20 * (1 + 1 + 0.15 + 1 + 1) = 0.83, which never clears the threshold. So
    the trap detector cannot fire on a default engine no matter how long the
    system sits still.

    Either lower CATATONIA_THRESHOLD below 0.83 or give G less weight.
    """
    engine = MetaGovernanceEngine(catatonia_window=4)
    pinned = dict(eta=1.0, A=1.0, G=0.14, C=1.0, R=1.0)
    for _ in range(10):
        result = engine.evaluate(AttractorState(**pinned))
    assert result.phi < engine.catatonia_threshold
    assert result.catatonia_risk is False


def test_catatonia_fires_once_the_weights_make_it_reachable():
    # de-weighting G lets phi clear 0.85 while novelty stays dead
    engine = MetaGovernanceEngine(
        weights={"eta": 0.25, "A": 0.25, "G": 0.0, "C": 0.25, "R": 0.25},
        catatonia_threshold=0.85,
        catatonia_window=4,
    )
    stuck = dict(eta=1.0, A=1.0, G=0.1, C=1.0, R=1.0)
    results = [engine.evaluate(AttractorState(**stuck)) for _ in range(4)]
    assert results[0].catatonia_risk is False, "a single high reading is not a trap"
    assert results[-1].catatonia_risk is True, "sustained high phi with dead G is"


def test_healthy_novelty_prevents_catatonia_even_at_high_phi():
    engine = MetaGovernanceEngine(
        weights={"eta": 0.25, "A": 0.25, "G": 0.0, "C": 0.25, "R": 0.25},
        catatonia_threshold=0.85,
        catatonia_window=4,
    )
    lively = dict(eta=1.0, A=1.0, G=0.9, C=1.0, R=1.0)
    for _ in range(6):
        result = engine.evaluate(AttractorState(**lively))
    assert result.phi >= 0.85, "phi is high, so only G keeps this healthy"
    assert result.catatonia_risk is False


# --- Layer -2: spatial nodes and fork/merge -----------------------------------

def test_ledger_digest_changes_as_events_are_recorded():
    node = SpatialNode()
    empty = node.ledger_digest()
    node.record({"kind": "observation"})
    assert node.ledger_digest() != empty


def test_merge_combines_both_ledgers_and_marks_parents_merged():
    engine = MetaGovernanceEngine()
    a = engine.fork_node()
    b = engine.fork_node()
    a.record({"n": 1})
    b.record({"n": 2})

    child = engine.merge(a.node_id, b.node_id)
    assert len(child.ledger) == 2
    assert a.merged is True and b.merged is True
    assert a.node_id in child.parent_id and b.node_id in child.parent_id


def test_a_merged_node_cannot_be_merged_again():
    a, b, c = SpatialNode(), SpatialNode(), SpatialNode()
    merge_nodes(a, b)
    with pytest.raises(ValueError):
        merge_nodes(a, c)


def test_status_counts_only_unmerged_nodes():
    engine = MetaGovernanceEngine()
    a = engine.fork_node()
    b = engine.fork_node()
    assert engine.status()["active_nodes"] == 2
    engine.merge(a.node_id, b.node_id)
    # the two parents are consumed, the child remains
    assert engine.status()["active_nodes"] == 1
