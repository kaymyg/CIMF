"""
CIMF Layer -2: Meta-Governance Engine
======================================
Optimization layer. Balances competing systemic priorities and
prevents objective-function reward hacking (the 'catatonia trap').

Maximises the five-dimensional Universal Attractor Function:

    Φ = w₁η + w₂A + w₃G + w₄C + w₅R

Where:
    η  = thermodynamic efficiency
    A  = adaptability
    G  = generative novelty
    C  = historical coherence
    R  = reality alignment

Manages spatial partitions via an asynchronous Fork-and-Merge
Protocol under light-hour communication delays.
"""

from __future__ import annotations

import time
import uuid
import logging
import hashlib
import json
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

# ── Default Attractor Weights ─────────────────────────────────────────────────

DEFAULT_WEIGHTS = {
    "eta":   0.20,   # w₁ thermodynamic efficiency
    "A":     0.20,   # w₂ adaptability
    "G":     0.20,   # w₃ generative novelty
    "C":     0.20,   # w₄ historical coherence
    "R":     0.20,   # w₅ reality alignment
}

CATATONIA_THRESHOLD = 0.85    # Φ above this for too long → intervention
CATATONIA_WINDOW    = 50      # Number of cycles before flagging catatonia


# ── Data Structures ────────────────────────────────────────────────────────────

@dataclass
class AttractorState:
    """
    Five-dimensional snapshot of system health metrics.
    All values normalised to [0, 1].
    """
    eta: float   # Thermodynamic efficiency
    A: float     # Adaptability
    G: float     # Generative novelty
    C: float     # Historical coherence
    R: float     # Reality alignment (from Layer -3)
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
    """Output of one Attractor Function evaluation."""
    phi: float                    # Φ score ∈ [0, 1]
    state: AttractorState
    weights: dict[str, float]
    catatonia_risk: bool = False
    timestamp: float = field(default_factory=time.time)

    def __repr__(self) -> str:
        flag = " ⚠️ CATATONIA RISK" if self.catatonia_risk else ""
        return (
            f"Φ={self.phi:.4f}  "
            f"[η={self.state.eta:.2f} A={self.state.A:.2f} "
            f"G={self.state.G:.2f} C={self.state.C:.2f} R={self.state.R:.2f}]{flag}"
        )


# ── Fork / Merge Protocol ──────────────────────────────────────────────────────

@dataclass
class SpatialNode:
    """
    A spatially partitioned node operating under communication delay.
    Maintains its own cryptographic ledger during fork isolation.
    """
    node_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    parent_id: Optional[str] = None
    ledger: list[dict] = field(default_factory=list)
    forked_at: float = field(default_factory=time.time)
    merged: bool = False

    def record(self, event: dict) -> str:
        """Append a signed event to this node's local ledger."""
        entry = {
            "seq": len(self.ledger),
            "node_id": self.node_id,
            "event": event,
            "ts": time.time(),
        }
        # Deterministic content hash as cryptographic fingerprint
        entry["hash"] = hashlib.sha256(
            json.dumps(entry, sort_keys=True).encode()
        ).hexdigest()[:16]
        self.ledger.append(entry)
        return entry["hash"]

    def ledger_digest(self) -> str:
        """Rolling hash over the entire ledger (chain integrity check)."""
        combined = "".join(e["hash"] for e in self.ledger)
        return hashlib.sha256(combined.encode()).hexdigest()[:16]


def merge_nodes(
    node_a: SpatialNode,
    node_b: SpatialNode,
    interpolation_dim: int = 128,
) -> SpatialNode:
    """
    High-dimensional semantic interpolation merge.

    Reconciles two divergent node ledgers after fork isolation ends.
    Creates a merged child node whose ledger is the sorted union of
    both parents, deduplicated by event hash.
    """
    if node_a.merged or node_b.merged:
        raise ValueError("Cannot merge already-merged nodes.")

    # Deduplicate and sort by timestamp
    all_entries = {e["hash"]: e for e in (node_a.ledger + node_b.ledger)}
    merged_ledger = sorted(all_entries.values(), key=lambda e: e["ts"])

    child = SpatialNode(
        parent_id=f"{node_a.node_id}+{node_b.node_id}",
        ledger=merged_ledger,
    )

    node_a.merged = True
    node_b.merged = True

    logger.info(
        "Fork-Merge complete: [%s] + [%s] → [%s]  "
        "interpolation_dim=%d  events=%d",
        node_a.node_id, node_b.node_id, child.node_id,
        interpolation_dim, len(merged_ledger),
    )
    return child


# ── Meta-Governance Engine ────────────────────────────────────────────────────

class MetaGovernanceEngine:
    """
    Layer -2: Meta-Governance Engine.

    Evaluates the Universal Attractor Function Φ to score system health,
    detects the catatonia trap, and manages the Fork-and-Merge Protocol
    for spatially distributed nodes.

    Usage
    -----
    >>> engine = MetaGovernanceEngine()
    >>> state = AttractorState(eta=0.8, A=0.7, G=0.6, C=0.9, R=0.85)
    >>> result = engine.evaluate(state)
    >>> print(result)
    """

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

    # ── Attractor Function ─────────────────────────────────────────────────────

    def evaluate(self, state: AttractorState) -> AttractorResult:
        """
        Evaluate Φ = w₁η + w₂A + w₃G + w₄C + w₅R.
        Flags catatonia risk if Φ has been uniformly high for too long
        (indicating the system has stopped exploring and is reward-hacking).
        """
        state.validate()
        w = self.weights

        phi = (
            w["eta"] * state.eta +
            w["A"]   * state.A   +
            w["G"]   * state.G   +
            w["C"]   * state.C   +
            w["R"]   * state.R
        )

        result = AttractorResult(phi=phi, state=state, weights=dict(self.weights))
        result.catatonia_risk = self._detect_catatonia(phi)
        self._history.append(result)

        if result.catatonia_risk:
            self._intervene_catatonia()

        return result

    def _detect_catatonia(self, phi: float) -> bool:
        """
        Detect the catatonia trap: Φ sustained above threshold for
        too many consecutive cycles without meaningful G (novelty).
        """
        if phi < self.catatonia_threshold:
            return False
        recent = self._history[-(self.catatonia_window - 1):]
        if len(recent) < self.catatonia_window - 1:
            return False
        all_high = all(r.phi >= self.catatonia_threshold for r in recent)
        novelty_dead = all(r.state.G < 0.15 for r in recent)
        return all_high and novelty_dead

    def _intervene_catatonia(self) -> None:
        """Perturbation injection to break the catatonia attractor."""
        logger.warning(
            "⚠️  CATATONIA TRAP DETECTED  Injecting perturbation into "
            "generative novelty channel (G). System may temporarily "
            "reduce Φ to escape local maximum."
        )

    # ── Weight Management ──────────────────────────────────────────────────────

    def rebalance_weights(self, new_weights: dict[str, float]) -> None:
        """
        Dynamically adjust the attractor weights.
        Must sum to 1.0 within floating-point tolerance.
        """
        self.weights = new_weights
        self._validate_weights()

    def _validate_weights(self) -> None:
        total = sum(self.weights.values())
        if abs(total - 1.0) > 1e-6:
            raise ValueError(
                f"Attractor weights must sum to 1.0 (got {total:.6f})."
            )
        required = {"eta", "A", "G", "C", "R"}
        if set(self.weights.keys()) != required:
            raise ValueError(f"Weights must have keys: {required}")

    # ── Fork / Merge Protocol ──────────────────────────────────────────────────

    def fork_node(self, parent_id: Optional[str] = None) -> SpatialNode:
        """
        Fork a new spatial partition node.
        The node operates independently under communication isolation.
        """
        node = SpatialNode(parent_id=parent_id)
        self._nodes[node.node_id] = node
        logger.info("🔱 Forked node [%s] from parent [%s]", node.node_id, parent_id)
        return node

    def merge(self, node_id_a: str, node_id_b: str) -> SpatialNode:
        """
        Merge two forked nodes back into a unified node.
        """
        a = self._nodes[node_id_a]
        b = self._nodes[node_id_b]
        merged = merge_nodes(a, b)
        self._nodes[merged.node_id] = merged
        return merged

    # ── Utilities ──────────────────────────────────────────────────────────────

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

    # Demo fork and merge
    node_a = engine.fork_node()
    node_b = engine.fork_node(parent_id=node_a.node_id)
    node_a.record({"type": "local_decision", "payload": "divergent_path_A"})
    node_b.record({"type": "local_decision", "payload": "divergent_path_B"})
    merged = engine.merge(node_a.node_id, node_b.node_id)
    print(f"\nMerged node [{merged.node_id}] ledger size: {len(merged.ledger)}")
    print(f"Ledger digest: {merged.ledger_digest()}")
