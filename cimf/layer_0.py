"""CIMF Layer 0: Entropy Governance Engine"""

from __future__ import annotations

import time
import logging
import math
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional

logger = logging.getLogger(__name__)


class Pipeline(Enum):
    GENERATIVE = auto()
    HYBRID_DELTA = auto()
    RAW_TOPO = auto()


ENTROPY_COSTS: dict[Pipeline, dict[str, float]] = {
    Pipeline.GENERATIVE:   {"write": 1.00, "metadata": 0.15, "retrieve": 0.80, "maintenance": 0.20},
    Pipeline.HYBRID_DELTA: {"write": 0.40, "metadata": 0.10, "retrieve": 0.35, "maintenance": 0.10},
    Pipeline.RAW_TOPO:     {"write": 0.10, "metadata": 0.02, "retrieve": 0.05, "maintenance": 0.01},
}

UP_MIGRATION_QUERY_THRESHOLD = 10
ADVERSARIAL_ENTROPY_THRESHOLD = 2.5


@dataclass
class WorkloadProfile:
    workload_id: str
    novelty: float
    compressibility: float
    query_frequency: float
    size_bytes: int
    timestamp: float = field(default_factory=time.time)


@dataclass
class TriageResult:
    workload_id: str
    assigned_pipeline: Pipeline
    posterior: dict[Pipeline, float]
    entropy_estimate: float
    timestamp: float = field(default_factory=time.time)

    def __repr__(self) -> str:
        probs = "  ".join(f"{p.name}={v:.2f}" for p, v in self.posterior.items())
        return (f"Triage[{self.workload_id[:8]}] -> {self.assigned_pipeline.name}"
                f"  S_est={self.entropy_estimate:.3f}  [{probs}]")


@dataclass
class EntropyLedgerEntry:
    asset_id: str
    pipeline: Pipeline
    s_write: float
    s_metadata: float
    s_retrieve: float
    s_maintenance: float
    query_count: int = 0
    migrated: bool = False
    timestamp: float = field(default_factory=time.time)

    @property
    def s_burden(self) -> float:
        return self.s_write + self.s_metadata + self.s_retrieve + self.s_maintenance

    def accrue_query(self, retrieve_cost_per_query: float) -> None:
        self.query_count += 1
        self.s_retrieve += retrieve_cost_per_query


class BayesianTriageClassifier:
    def __init__(self, priors: Optional[dict[Pipeline, float]] = None) -> None:
        self._priors = priors or {
            Pipeline.GENERATIVE: 0.20,
            Pipeline.HYBRID_DELTA: 0.50,
            Pipeline.RAW_TOPO: 0.30,
        }
        self._observation_counts: dict[Pipeline, int] = {p: 0 for p in Pipeline}

    def classify(self, profile: WorkloadProfile) -> TriageResult:
        likelihoods = {
            Pipeline.GENERATIVE: self._likelihood_generative(profile),
            Pipeline.HYBRID_DELTA: self._likelihood_hybrid(profile),
            Pipeline.RAW_TOPO: self._likelihood_raw_topo(profile),
        }
        unnorm = {p: likelihoods[p] * self._priors[p] for p in Pipeline}
        total = sum(unnorm.values()) or 1e-12
        posterior = {p: v / total for p, v in unnorm.items()}
        chosen = max(posterior, key=posterior.__getitem__)
        self._update_prior(chosen)
        costs = ENTROPY_COSTS[chosen]
        size_factor = math.log1p(profile.size_bytes) / math.log1p(1e6)
        entropy_est = sum(costs.values()) * size_factor
        return TriageResult(profile.workload_id, chosen, posterior, entropy_est)

    def _likelihood_generative(self, p: WorkloadProfile) -> float:
        return p.novelty * (1 - p.compressibility) + 0.05

    def _likelihood_hybrid(self, p: WorkloadProfile) -> float:
        balance = 1.0 - abs(p.novelty - 0.5) - abs(p.compressibility - 0.5)
        return max(0.0, balance) + 0.10

    def _likelihood_raw_topo(self, p: WorkloadProfile) -> float:
        return (1 - p.novelty) * p.compressibility + 0.05

    def _update_prior(self, chosen: Pipeline) -> None:
        self._observation_counts[chosen] += 1
        total = sum(self._observation_counts.values()) + len(Pipeline)
        for p in Pipeline:
            self._priors[p] = (self._observation_counts[p] + 1) / total


class EntropyGovernanceEngine:
    def __init__(self) -> None:
        self._classifier = BayesianTriageClassifier()
        self._ledger: dict[str, EntropyLedgerEntry] = {}
        self._total_burden: float = 0.0
        self._adversarial_events: int = 0

    def ingest(self, profile: WorkloadProfile) -> TriageResult:
        result = self._classifier.classify(profile)
        costs = ENTROPY_COSTS[result.assigned_pipeline]
        size_f = math.log1p(profile.size_bytes) / math.log1p(1e6)
        entry = EntropyLedgerEntry(
            asset_id=profile.workload_id,
            pipeline=result.assigned_pipeline,
            s_write=costs["write"] * size_f,
            s_metadata=costs["metadata"] * size_f,
            s_retrieve=0.0,
            s_maintenance=costs["maintenance"] * size_f,
        )
        self._ledger[profile.workload_id] = entry
        self._total_burden += entry.s_burden
        self._check_adversarial(result.entropy_estimate)
        logger.debug("%s", result)
        return result

    def query_asset(self, asset_id: str) -> EntropyLedgerEntry:
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

    def _up_migrate(self, entry: EntropyLedgerEntry) -> None:
        entry.migrated = True
        migration_cost = ENTROPY_COSTS[Pipeline.RAW_TOPO]["write"] * 0.5
        self._total_burden += migration_cost
        logger.info("Up-migration triggered for [%s]  queries=%d  migration_cost=%.4f",
                    entry.asset_id, entry.query_count, migration_cost)

    def _check_adversarial(self, entropy_estimate: float) -> None:
        if entropy_estimate > ADVERSARIAL_ENTROPY_THRESHOLD:
            self._adversarial_events += 1
            logger.warning("ADVERSARIAL ENTROPY INJECTION DETECTED  S_est=%.3f > threshold=%.3f  event #%d",
                           entropy_estimate, ADVERSARIAL_ENTROPY_THRESHOLD, self._adversarial_events)

    def lifetime_burden(self) -> float:
        return self._total_burden

    def burden_breakdown(self) -> dict:
        total = {"s_write": 0.0, "s_metadata": 0.0, "s_retrieve": 0.0, "s_maintenance": 0.0}
        for e in self._ledger.values():
            total["s_write"] += e.s_write
            total["s_metadata"] += e.s_metadata
            total["s_retrieve"] += e.s_retrieve
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
    profiles = [
        WorkloadProfile("cosmic_obs_001", 0.95, 0.05, 5.0, 512_000),
        WorkloadProfile("delta_record_002", 0.45, 0.60, 1.0, 8_192),
        WorkloadProfile("topo_raw_003", 0.10, 0.90, 0.1, 1_024),
    ]
    for p in profiles:
        print(engine.ingest(p))
    for _ in range(12):
        engine.query_asset("cosmic_obs_001")
    print("\n", engine.status())
