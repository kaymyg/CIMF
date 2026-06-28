"""
CIMF Layer 0: Entropy Governance Engine
========================================
Thermodynamics layer. Regulates the system's operational thermal
footprint and defends against adversarial entropy injection.

Utilises a Probabilistic Bayesian Estimator to triage incoming
workloads into three distinct pipelines:

    - GENERATIVE   → High novelty, high entropy cost
    - HYBRID_DELTA → Partial reconstruction from stored deltas
    - RAW_TOPO     → Raw topological pass-through (minimal entropy)

Tracks the comprehensive Lifetime Entropy Burden:

    S_burden = S_write + S_metadata + S_retrieve + S_maintenance

Highly-queried assets are triggered for thermodynamic up-migration
into less-compressed caches.
"""

from __future__ import annotations

import time
import logging
import math
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional

logger = logging.getLogger(__name__)

# ── Pipeline Enum ─────────────────────────────────────────────────────────────

class Pipeline(Enum):
    GENERATIVE   = auto()    # Full generative reconstruction
    HYBRID_DELTA = auto()    # Delta-based partial reconstruction
    RAW_TOPO     = auto()    # Raw topological pass-through


# ── Entropy Cost Model ────────────────────────────────────────────────────────
#
# Relative entropy costs per pipeline (in normalised Landauer units).
# 1.0 Landauer unit = kT·ln(2) ≈ 2.85×10⁻²¹ J at T=300K

ENTROPY_COSTS: dict[Pipeline, dict[str, float]] = {
    Pipeline.GENERATIVE:   {"write": 1.00, "metadata": 0.15, "retrieve": 0.80, "maintenance": 0.20},
    Pipeline.HYBRID_DELTA: {"write": 0.40, "metadata": 0.10, "retrieve": 0.35, "maintenance": 0.10},
    Pipeline.RAW_TOPO:     {"write": 0.10, "metadata": 0.02, "retrieve": 0.05, "maintenance": 0.01},
}

UP_MIGRATION_QUERY_THRESHOLD = 10    # Queries before triggering up-migration
ADVERSARIAL_ENTROPY_THRESHOLD = 2.5  # Burst entropy above this → adversarial flag


# ── Data Structures ────────────────────────────────────────────────────────────

@dataclass
class WorkloadProfile:
    """
    Characterisation of an incoming workload for Bayesian triage.
    """
    workload_id:   str
    novelty:       float       # [0, 1] how novel is this data?
    compressibility: float     # [0, 1] how well does it compress?
    query_frequency: float     # Expected queries per epoch
    size_bytes:    int
    timestamp:     float = field(default_factory=time.time)


@dataclass
class TriageResult:
    """Output of the Bayesian triage classifier."""
    workload_id: str
    assigned_pipeline: Pipeline
    posterior: dict[Pipeline, float]   # P(pipeline | workload)
    entropy_estimate: float            # Expected S_burden for this workload
    timestamp: float = field(default_factory=time.time)

    def __repr__(self) -> str:
        probs = "  ".join(
            f"{p.name}={v:.2f}" for p, v in self.posterior.items()
        )
        return (
            f"Triage[{self.workload_id[:8]}] → {self.assigned_pipeline.name}"
            f"  S_est={self.entropy_estimate:.3f}  [{probs}]"
        )


@dataclass
class EntropyLedgerEntry:
    """A single entry in the Lifetime Entropy Ledger."""
    asset_id:       str
    pipeline:       Pipeline
    s_write:        float
    s_metadata:     float
    s_retrieve:     float
    s_maintenance:  float
    query_count:    int = 0
    migrated:       bool = False
    timestamp:      float = field(default_factory=time.time)

    @property
    def s_burden(self) -> float:
        """S_burden = S_write + S_metadata + S_retrieve + S_maintenance"""
        return self.s_write + self.s_metadata + self.s_retrieve + self.s_maintenance

    def accrue_query(self, retrieve_cost_per_query: float) -> None:
        """Register one query against this asset."""
        self.query_count += 1
        self.s_retrieve += retrieve_cost_per_query


# ── Bayesian Triage Classifier ────────────────────────────────────────────────

class BayesianTriageClassifier:
    """
    Probabilistic Bayesian Estimator for pipeline assignment.

    Prior beliefs about pipeline frequency can be updated as the
    system observes real workload distributions over time.
    """

    def __init__(self, priors: Optional[dict[Pipeline, float]] = None) -> None:
        self._priors = priors or {
            Pipeline.GENERATIVE:   0.20,
            Pipeline.HYBRID_DELTA: 0.50,
            Pipeline.RAW_TOPO:     0.30,
        }
        self._observation_counts: dict[Pipeline, int] = {p: 0 for p in Pipeline}

    def classify(self, profile: WorkloadProfile) -> TriageResult:
        """
        Assign a pipeline via Bayesian posterior:

            P(pipeline | workload) ∝ P(workload | pipeline) × P(pipeline)

        Likelihood heuristics:
            GENERATIVE   → high novelty, low compressibility
            HYBRID_DELTA → moderate novelty, moderate compressibility
            RAW_TOPO     → low novelty, high compressibility
        """
        likelihoods = {
            Pipeline.GENERATIVE:   self._likelihood_generative(profile),
            Pipeline.HYBRID_DELTA: self._likelihood_hybrid(profile),
            Pipeline.RAW_TOPO:     self._likelihood_raw_topo(profile),
        }

        unnorm = {p: likelihoods[p] * self._priors[p] for p in Pipeline}
        total  = sum(unnorm.values()) or 1e-12
        posterior = {p: v / total for p, v in unnorm.items()}

        chosen = max(posterior, key=posterior.__getitem__)
        self._update_prior(chosen)

        costs = ENTROPY_COSTS[chosen]
        size_factor = math.log1p(profile.size_bytes) / math.log1p(1e6)
        entropy_est = sum(costs.values()) * size_factor

        return TriageResult(
            workload_id=profile.workload_id,
            assigned_pipeline=chosen,
            posterior=posterior,
            entropy_estimate=entropy_est,
        )

    def _likelihood_generative(self, p: WorkloadProfile) -> float:
        return p.novelty * (1 - p.compressibility) + 0.05

    def _likelihood_hybrid(self, p: WorkloadProfile) -> float:
        balance = 1.0 - abs(p.novelty - 0.5) - abs(p.compressibility - 0.5)
        return max(0.0, balance) + 0.10

    def _likelihood_raw_topo(self, p: WorkloadProfile) -> float:
        return (1 - p.novelty) * p.compressibility + 0.05

    def _update_prior(self, chosen: Pipeline) -> None:
        """Bayesian prior update — simple additive smoothing."""
        self._observation_counts[chosen] += 1
        total = sum(self._observation_counts.values()) + len(Pipeline)
        for p in Pipeline:
            self._priors[p] = (self._observation_counts[p] + 1) / total


# ── Entropy Governance Engine ─────────────────────────────────────────────────

class EntropyGovernanceEngine:
    """
    Layer 0: Entropy Governance Engine.

    Classifies workloads, maintains the Lifetime Entropy Ledger,
    detects adversarial entropy injection, and triggers
    up-migration for hot assets.

    Usage
    -----
    >>> engine = EntropyGovernanceEngine()
    >>> profile = WorkloadProfile("w001", novelty=0.9, compressibility=0.1,
    ...                           query_frequency=2.0, size_bytes=4096)
    >>> result = engine.ingest(profile)
    >>> print(result)
    """

    def __init__(self) -> None:
        self._classifier = BayesianTriageClassifier()
        self._ledger: dict[str, EntropyLedgerEntry] = {}
        self._total_burden: float = 0.0
        self._adversarial_events: int = 0

    # ── Ingestion ──────────────────────────────────────────────────────────────

    def ingest(self, profile: WorkloadProfile) -> TriageResult:
        """
        Classify a workload and register it in the entropy ledger.
        """
        result = self._classifier.classify(profile)
        costs  = ENTROPY_COSTS[result.assigned_pipeline]
        size_f = math.log1p(profile.size_bytes) / math.log1p(1e6)

        entry = EntropyLedgerEntry(
            asset_id=profile.workload_id,
            pipeline=result.assigned_pipeline,
            s_write=costs["write"]       * size_f,
            s_metadata=costs["metadata"] * size_f,
            s_retrieve=0.0,
            s_maintenance=costs["maintenance"] * size_f,
        )

        self._ledger[profile.workload_id] = entry
        self._total_burden += entry.s_burden

        self._check_adversarial(result.entropy_estimate)

        logger.debug("📊 %s", result)
        return result

    # ── Query Accounting ───────────────────────────────────────────────────────

    def query_asset(self, asset_id: str) -> EntropyLedgerEntry:
        """
        Register a read/query against a stored asset.
        Reads are active computational expenditures in CIMF.
        Triggers up-migration if the asset is queried too frequently.
        """
        if asset_id not in self._ledger:
            raise KeyError(f"Asset '{asset_id}' not found in ledger.")

        entry = self._ledger[asset_id]
        costs = ENTROPY_COSTS[entry.pipeline]
        size_f = 1.0
        entry.accrue_query(retrieve_cost_per_query=costs["retrieve"] * size_f * 0.1)
        self._total_burden += costs["retrieve"] * size_f * 0.1

        if entry.query_count >= UP_MIGRATION_QUERY_THRESHOLD and not entry.migrated:
            self._up_migrate(entry)

        return entry

    # ── Up-Migration ───────────────────────────────────────────────────────────

    def _up_migrate(self, entry: EntropyLedgerEntry) -> None:
        """
        Thermodynamic up-migration: move a hot asset into a faster,
        less-compressed cache tier. This lowers future retrieve costs
        at the expense of a one-time migration write cost.
        """
        entry.migrated = True
        migration_cost = ENTROPY_COSTS[Pipeline.RAW_TOPO]["write"] * 0.5
        self._total_burden += migration_cost
        logger.info(
            "⬆️  Up-migration triggered for [%s]  "
            "queries=%d  migration_cost=%.4f",
            entry.asset_id, entry.query_count, migration_cost
        )

    # ── Adversarial Detection ──────────────────────────────────────────────────

    def _check_adversarial(self, entropy_estimate: float) -> None:
        if entropy_estimate > ADVERSARIAL_ENTROPY_THRESHOLD:
            self._adversarial_events += 1
            logger.warning(
                "🚨 ADVERSARIAL ENTROPY INJECTION DETECTED  "
                "S_est=%.3f > threshold=%.3f  event #%d",
                entropy_estimate, ADVERSARIAL_ENTROPY_THRESHOLD,
                self._adversarial_events
            )

    # ── Ledger Reporting ───────────────────────────────────────────────────────

    def lifetime_burden(self) -> float:
        """Total accumulated entropy burden across all assets."""
        return self._total_burden

    def burden_breakdown(self) -> dict:
        total = {"s_write": 0.0, "s_metadata": 0.0, "s_retrieve": 0.0, "s_maintenance": 0.0}
        for e in self._ledger.values():
            total["s_write"]       += e.s_write
            total["s_metadata"]    += e.s_metadata
            total["s_retrieve"]    += e.s_retrieve
            total["s_maintenance"] += e.s_maintenance
        return total

    def status(self) -> dict:
        return {
            "layer": 0,
            "name": "Entropy Governance Engine",
            "assets_tracked": len(self._ledger),
            "total_s_burden": self._total_burden,
            "breakdown": self.burden_breakdown(),
            "adversarial_events": self._adversarial_events,
            "migrated_assets": sum(1 for e in self._ledger.values() if e.migrated),
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    engine = EntropyGovernanceEngine()

    # Ingest workloads of varying character
    profiles = [
        WorkloadProfile("cosmic_obs_001", novelty=0.95, compressibility=0.05, query_frequency=5.0, size_bytes=512_000),
        WorkloadProfile("delta_record_002", novelty=0.45, compressibility=0.60, query_frequency=1.0, size_bytes=8_192),
        WorkloadProfile("topo_raw_003", novelty=0.10, compressibility=0.90, query_frequency=0.1, size_bytes=1_024),
    ]

    for p in profiles:
        r = engine.ingest(p)
        print(r)

    # Simulate heavy querying of asset 001
    for _ in range(12):
        engine.query_asset("cosmic_obs_001")

    print("\n", engine.status())
