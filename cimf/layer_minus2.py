"""CIMF Layer -2: Meta-Governance Engine"""

from __future__ import annotations

import time
import uuid
import logging
import hashlib
import json
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

DEFAULT_WEIGHTS = {"eta": 0.20, "A": 0.20, "G": 0.20, "C": 0.20, "R": 0.20}
CATATONIA_THRESHOLD = 0.85
CATATONIA_WINDOW = 50


@dataclass
class AttractorState:
    eta: float
    A: float
    G: float
    C: float
    R: float
    timestamp: float = field(default_factory=time.time)

    def validate(self) -> None:
        for attr in ("eta", "A", "G", "C", "R"):
            val = getattr(self, attr)
            if not (0.0 <= val <= 1.0):
                raise ValueError(f"AttractorState.{attr}={val} out of [0,1].")

    def to_dict(self) -> dict:
        return {"eta": self.eta, "A": self.A, "G": self.G, "C": self.C, "R": self.R}


@dataclass
class AttractorResult:
    phi: float
    state: AttractorState
    weights: dict[str, float]
    catatonia_risk: bool = False
    timestamp: float = field(default_factory=time.time)

    def __repr__(self) -> str:
        flag = " CATATONIA RISK" if self.catatonia_risk else ""
        return (
            f"Phi={self.phi:.4f}  "
            f"[eta={self.state.eta:.2f} A={self.state.A:.2f} "
            f"G={self.state.G:.2f} C={self.state.C:.2f} R={self.state.R:.2f}]{flag}"
        )


@dataclass
class SpatialNode:
    node_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    parent_id: Optional[str] = None
    ledger: list[dict] = field(default_factory=list)
    forked_at: float = field(default_factory=time.time)
    merged: bool = False

    def record(self, event: dict) -> str:
        entry = {
            "seq": len(self.ledger),
            "node_id": self.node_id,
            "event": event,
            "ts": time.time(),
        }
        entry["hash"] = hashlib.sha256(
            json.dumps(entry, sort_keys=True).encode()
        ).hexdigest()[:16]
        self.ledger.append(entry)
        return entry["hash"]

    def ledger_digest(self) -> str:
        combined = "".join(e["hash"] for e in self.ledger)
        return hashlib.sha256(combined.encode()).hexdigest()[:16]


def merge_nodes(node_a: SpatialNode, node_b: SpatialNode, interpolation_dim: int = 128) -> SpatialNode:
    if node_a.merged or node_b.merged:
        raise ValueError("Cannot merge already-merged nodes.")
    all_entries = {e["hash"]: e for e in (node_a.ledger + node_b.ledger)}
    merged_ledger = sorted(all_entries.values(), key=lambda e: e["ts"])
    child = SpatialNode(parent_id=f"{node_a.node_id}+{node_b.node_id}", ledger=merged_ledger)
    node_a.merged = True
    node_b.merged = True
    logger.info(
        "Fork-Merge complete: [%s] + [%s] -> [%s]  interpolation_dim=%d  events=%d",
        node_a.node_id, node_b.node_id, child.node_id, interpolation_dim, len(merged_ledger),
    )
    return child


class MetaGovernanceEngine:
    def __init__(
        self,
        weights: Optional[dict[str, float]] = None,
        catatonia_threshold: float = CATATONIA_THRESHOLD,
        catatonia_window: int = CATATONIA_WINDOW,
    ) -> None:
        self.weights = weights or dict(DEFAULT_WEIGHTS)
        self._validate_weights()
        self.catatonia_threshold = catatonia_threshold
        self.catatonia_window = catatonia_window
        self._history: list[AttractorResult] = []
        self._nodes: dict[str, SpatialNode] = {}

    def evaluate(self, state: AttractorState) -> AttractorResult:
        state.validate()
        w = self.weights
        phi = (w["eta"] * state.eta + w["A"] * state.A + w["G"] * state.G
               + w["C"] * state.C + w["R"] * state.R)
        result = AttractorResult(phi=phi, state=state, weights=dict(self.weights))
        result.catatonia_risk = self._detect_catatonia(phi)
        self._history.append(result)
        if result.catatonia_risk:
            self._intervene_catatonia()
        return result

    def _detect_catatonia(self, phi: float) -> bool:
        if phi < self.catatonia_threshold:
            return False
        recent = self._history[-(self.catatonia_window - 1):]
        if len(recent) < self.catatonia_window - 1:
            return False
        all_high = all(r.phi >= self.catatonia_threshold for r in recent)
        novelty_dead = all(r.state.G < 0.15 for r in recent)
        return all_high and novelty_dead

    def _intervene_catatonia(self) -> None:
        logger.warning(
            "CATATONIA TRAP DETECTED  Injecting perturbation into "
            "generative novelty channel (G)."
        )

    def rebalance_weights(self, new_weights: dict[str, float]) -> None:
        # Validate against the candidate but roll back on rejection: assigning
        # first left the engine holding invalid weights whenever this raised.
        previous = self.weights
        self.weights = new_weights
        try:
            self._validate_weights()
        except ValueError:
            self.weights = previous
            raise

    def _validate_weights(self) -> None:
        total = sum(self.weights.values())
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"Attractor weights must sum to 1.0 (got {total:.6f}).")
        required = {"eta", "A", "G", "C", "R"}
        if set(self.weights.keys()) != required:
            raise ValueError(f"Weights must have keys: {required}")

    def fork_node(self, parent_id: Optional[str] = None) -> SpatialNode:
        node = SpatialNode(parent_id=parent_id)
        self._nodes[node.node_id] = node
        logger.info("Forked node [%s] from parent [%s]", node.node_id, parent_id)
        return node

    def merge(self, node_id_a: str, node_id_b: str) -> SpatialNode:
        a = self._nodes[node_id_a]
        b = self._nodes[node_id_b]
        merged = merge_nodes(a, b)
        self._nodes[merged.node_id] = merged
        return merged

    @property
    def phi_history(self) -> list[float]:
        return [r.phi for r in self._history]

    def phi_moving_average(self, window: int = 10) -> float | None:
        vals = self.phi_history[-window:]
        return sum(vals) / len(vals) if vals else None

    def status(self) -> dict:
        last = self._history[-1] if self._history else None
        return {
            "layer": -2,
            "name": "Meta-Governance Engine",
            "phi": last.phi if last else None,
            "catatonia_risk": last.catatonia_risk if last else None,
            "weights": self.weights,
            "active_nodes": sum(1 for n in self._nodes.values() if not n.merged),
            "total_nodes": len(self._nodes),
            "evaluation_cycles": len(self._history),
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    engine = MetaGovernanceEngine()
    state = AttractorState(eta=0.82, A=0.75, G=0.60, C=0.90, R=0.88)
    result = engine.evaluate(state)
    print(result)
    print(engine.status())
    node_a = engine.fork_node()
    node_b = engine.fork_node(parent_id=node_a.node_id)
    node_a.record({"type": "local_decision", "payload": "divergent_path_A"})
    node_b.record({"type": "local_decision", "payload": "divergent_path_B"})
    merged = engine.merge(node_a.node_id, node_b.node_id)
    print(f"\nMerged node [{merged.node_id}] ledger size: {len(merged.ledger)}")
    print(f"Ledger digest: {merged.ledger_digest()}")
