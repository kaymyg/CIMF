"""CIMF Layers 1-3: Physical & Architectural Storage Core"""

from __future__ import annotations

import math
import zlib
import uuid
import logging
import hashlib
import random
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional

logger = logging.getLogger(__name__)


class ReconstructionModel(Enum):
    GENERATIVE = auto()
    DELTA = auto()
    VERBATIM = auto()


@dataclass
class EnergyMinimum:
    state_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    coordinates: list[float] = field(default_factory=list)
    energy: float = 0.0
    model: ReconstructionModel = ReconstructionModel.GENERATIVE
    kolmogorov_complexity: float = 0.0
    created_at: float = field(default_factory=time.time)

    def encode(self, data: bytes) -> None:
        n_dims = 64
        seed = int(hashlib.sha256(data).hexdigest(), 16)
        rng = random.Random(seed)
        self.coordinates = [rng.gauss(0, 1) for _ in range(n_dims)]
        norm = math.sqrt(sum(x**2 for x in self.coordinates)) or 1.0
        self.coordinates = [x / norm for x in self.coordinates]
        # Compression ratio as a cheap, CONTENT-sensitive K(x) proxy.
        # The previous energy formula -log(len/max(len,1)) was identically 0.0
        # for every non-empty input, and K = log2(len+1) depended only on length
        # -- so b"x"*100 and 100 random bytes scored identically.
        if data:
            compressed = len(zlib.compress(data, level=6))
            ratio = compressed / len(data)
            self.energy = -math.log(max(ratio, 1e-9))
            self.kolmogorov_complexity = compressed * 8.0 / len(data)
        else:
            self.energy = 0.0
            self.kolmogorov_complexity = 0.0

    def distance_to(self, other: "EnergyMinimum") -> float:
        if len(self.coordinates) != len(other.coordinates):
            raise ValueError("Dimensionality mismatch.")
        return math.sqrt(sum((a - b)**2 for a, b in zip(self.coordinates, other.coordinates)))


class AdaptiveCompressionLayer:
    def __init__(self) -> None:
        self._store: dict[str, EnergyMinimum] = {}

    def store(self, data: bytes) -> str:
        em = EnergyMinimum()
        em.encode(data)
        # Thresholds are now in bits/byte (0 = perfectly compressible,
        # 8 = incompressible/random), matching the new K estimate. The old
        # 8/20 cutoffs were length-derived, making VERBATIM unreachable
        # below 1 MB regardless of how random the content actually was.
        if em.kolmogorov_complexity < 2.0:
            em.model = ReconstructionModel.GENERATIVE
        elif em.kolmogorov_complexity < 6.0:
            em.model = ReconstructionModel.DELTA
        else:
            em.model = ReconstructionModel.VERBATIM
        self._store[em.state_id] = em
        logger.debug("L3 store [%s]  K=%.2f  model=%s  energy=%.4f",
                     em.state_id, em.kolmogorov_complexity, em.model.name, em.energy)
        return em.state_id

    def nearest_attractor(self, state_id: str) -> Optional[str]:
        if state_id not in self._store:
            return None
        target = self._store[state_id]
        best_id, best_dist = None, float("inf")
        for sid, em in self._store.items():
            if sid == state_id:
                continue
            d = target.distance_to(em)
            if d < best_dist:
                best_dist, best_id = d, sid
        return best_id

    def status(self) -> dict:
        return {
            "layer": 3,
            "name": "Adaptive Workload Compression",
            "stored_states": len(self._store),
            "model_distribution": {
                m.name: sum(1 for e in self._store.values() if e.model == m)
                for m in ReconstructionModel
            },
        }


@dataclass
class MembraneNode:
    node_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    depth: int = 0
    children: list["MembraneNode"] = field(default_factory=list)
    surface_area: float = 1.0
    q_export: float = 0.0

    def radiate(self, entropy_load: float) -> float:
        capacity = self.surface_area * 0.8
        exported = min(entropy_load, capacity)
        self.q_export += exported
        return exported


class FractalMembraneNetwork:
    def __init__(self, branching_factor: int = 3, max_depth: int = 5,
                 scale_factor: float = 2.0) -> None:
        self.branching_factor = branching_factor
        self.max_depth = max_depth
        # 1/r for box-counting, independent of N (= branching_factor). The old
        # hausdorff_dimension() computed log(N)/log(N), which is exactly 1.0 for
        # every branching factor. With N=3, r=1/2 this yields D_H ~= 1.585;
        # N=7, r=1/3 yields 1.771, inside the README's 1.7-1.9 target band.
        self.scale_factor = scale_factor
        self._root = self._build_tree(depth=0)
        self._all_nodes = self._flatten(self._root)

    def _build_tree(self, depth: int) -> MembraneNode:
        node = MembraneNode(depth=depth)
        node.surface_area = (self.branching_factor ** depth) * 0.1
        if depth < self.max_depth:
            node.children = [self._build_tree(depth + 1) for _ in range(self.branching_factor)]
        return node

    def _flatten(self, node: MembraneNode) -> list[MembraneNode]:
        result = [node]
        for child in node.children:
            result.extend(self._flatten(child))
        return result

    @property
    def total_surface_area(self) -> float:
        return sum(n.surface_area for n in self._all_nodes)

    def export_entropy(self, total_load: float) -> float:
        leaf_nodes = [n for n in self._all_nodes if not n.children]
        if not leaf_nodes:
            return 0.0
        load_per_leaf = total_load / len(leaf_nodes)
        total_exported = sum(n.radiate(load_per_leaf) for n in leaf_nodes)
        logger.debug("L2 entropy export: load=%.4f  exported=%.4f  efficiency=%.2f%%",
                     total_load, total_exported, 100 * total_exported / max(total_load, 1e-12))
        return total_exported / max(total_load, 1e-12)

    def hausdorff_dimension(self) -> float:
        """Box-counting dimension D_H = log(N) / log(1/r)."""
        return math.log(self.branching_factor) / math.log(self.scale_factor)

    def status(self) -> dict:
        return {
            "layer": 2,
            "name": "Fractal Gossamer Membrane Network",
            "total_nodes": len(self._all_nodes),
            "leaf_nodes": sum(1 for n in self._all_nodes if not n.children),
            "total_surface_area": self.total_surface_area,
            "max_depth": self.max_depth,
            "branching_factor": self.branching_factor,
            "total_q_exported": sum(n.q_export for n in self._all_nodes),
        }


class FaultDomainTier(Enum):
    TOPOLOGICAL = auto()
    CLASSICAL = auto()
    GLOBAL = auto()


@dataclass
class FaultDomain:
    domain_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    tier: FaultDomainTier = FaultDomainTier.CLASSICAL
    data_shards: list[str] = field(default_factory=list)
    error_rate: float = 0.0
    active: bool = True

    def check_parity(self) -> bool:
        if self.tier == FaultDomainTier.TOPOLOGICAL:
            return random.random() > 0.0001
        elif self.tier == FaultDomainTier.CLASSICAL:
            return random.random() > 0.01
        else:
            return random.random() > 0.05

    def correct(self) -> bool:
        if self.tier == FaultDomainTier.TOPOLOGICAL:
            return True
        elif self.tier == FaultDomainTier.CLASSICAL:
            return random.random() < 0.999
        else:
            return random.random() < 0.99


class MultiscaleFaultDomainManager:
    def __init__(self, n_topological: int = 8, n_classical: int = 4, n_global: int = 2) -> None:
        self._domains: dict[FaultDomainTier, list[FaultDomain]] = {
            FaultDomainTier.TOPOLOGICAL: [FaultDomain(tier=FaultDomainTier.TOPOLOGICAL) for _ in range(n_topological)],
            FaultDomainTier.CLASSICAL: [FaultDomain(tier=FaultDomainTier.CLASSICAL) for _ in range(n_classical)],
            FaultDomainTier.GLOBAL: [FaultDomain(tier=FaultDomainTier.GLOBAL) for _ in range(n_global)],
        }
        self._correction_log: list[dict] = []

    def store_shard(self, data_id: str) -> None:
        for tier_domains in self._domains.values():
            for domain in tier_domains:
                domain.data_shards.append(data_id)

    def run_integrity_sweep(self) -> dict:
        results = {}
        for tier, domains in self._domains.items():
            tier_results = []
            for domain in domains:
                passed = domain.check_parity()
                corrected = None
                if not passed:
                    corrected = domain.correct()
                    self._correction_log.append({
                        "domain_id": domain.domain_id, "tier": tier.name,
                        "corrected": corrected, "ts": time.time(),
                    })
                    logger.warning("Parity failure in [%s/%s]  corrected=%s", tier.name, domain.domain_id, corrected)
                tier_results.append({"domain_id": domain.domain_id, "ok": passed, "corrected": corrected})
            results[tier.name] = tier_results
        return results

    def status(self) -> dict:
        total_shards = sum(len(d.data_shards) for domains in self._domains.values() for d in domains)
        return {
            "layer": 1,
            "name": "Multiscale Fault Domains",
            "domain_counts": {t.name: len(d) for t, d in self._domains.items()},
            "total_shard_replicas": total_shards,
            "correction_events": len(self._correction_log),
        }


class PhysicalStorageCore:
    def __init__(self) -> None:
        self.l3 = AdaptiveCompressionLayer()
        self.l2 = FractalMembraneNetwork()
        self.l1 = MultiscaleFaultDomainManager()

    def write(self, data: bytes) -> str:
        state_id = self.l3.store(data)
        self.l1.store_shard(state_id)
        entropy_load = math.log1p(len(data)) / 10
        self.l2.export_entropy(entropy_load)
        logger.info("Physical write complete: state_id=%s", state_id)
        return state_id

    def integrity_check(self) -> dict:
        return self.l1.run_integrity_sweep()

    def status(self) -> dict:
        return {"l3": self.l3.status(), "l2": self.l2.status(), "l1": self.l1.status()}


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    core = PhysicalStorageCore()
    for payload in [b"Cosmic epoch 4471 observation data.", b"x" * 100_000, b"hi"]:
        sid = core.write(payload)
        print(f"Written: {sid}")
    print("\nIntegrity sweep:")
    sweep = core.integrity_check()
    print("\nStatus:")
    import json
    print(json.dumps(core.status(), indent=2))
