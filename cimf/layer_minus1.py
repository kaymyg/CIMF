"""
CIMF Layer -1: Coherence & Identity Engine
===========================================
Continuity layer. Preserves the core self-consistency of the
intelligence while preventing semantic extinction — 'Meaning Rot'.

Enforces a strict metric tensor limit on structural changes using
a dynamic Identity Plasticity Budget λ(t):

    d( I(t+Δt), I(t) ) ≤ λ(t)

Information is packaged into Immutable Semantic Containers (ISCs)
that anchor a raw data seed, its delta, a localised model snapshot,
and a deterministic execution proof — ensuring compatibility across
changing substrates over deep time.
"""

from __future__ import annotations

import time
import uuid
import hashlib
import json
import logging
import math
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

DEFAULT_LAMBDA_INITIAL  = 0.10    # Initial plasticity budget (10% change allowed)
DEFAULT_LAMBDA_DECAY    = 0.005   # Budget tightens per epoch as system matures
DEFAULT_LAMBDA_MIN      = 0.005   # Floor — prevents total rigidity
MEANING_ROT_THRESHOLD   = 0.30    # Semantic drift above this → Meaning Rot alert


# ── Identity Manifold ─────────────────────────────────────────────────────────

@dataclass
class IdentityVector:
    """
    A high-dimensional snapshot of the system's semantic identity.
    Represented as a named dictionary of normalised feature dimensions.
    """
    features: dict[str, float]
    version: int = 0
    timestamp: float = field(default_factory=time.time)

    def distance(self, other: "IdentityVector") -> float:
        """
        Euclidean distance in the shared feature space.
        Missing keys in either vector are treated as 0.
        Normalised to [0, 1] by the number of dimensions.
        """
        all_keys = set(self.features) | set(other.features)
        if not all_keys:
            return 0.0
        sq_sum = sum(
            (self.features.get(k, 0.0) - other.features.get(k, 0.0)) ** 2
            for k in all_keys
        )
        return math.sqrt(sq_sum / len(all_keys))

    def __repr__(self) -> str:
        dims = ", ".join(f"{k}={v:.3f}" for k, v in self.features.items())
        return f"IdentityVector(v{self.version}, [{dims}])"


# ── Plasticity Budget ─────────────────────────────────────────────────────────

class PlasticityBudget:
    """
    Dynamic Identity Plasticity Budget λ(t).
    Starts permissive during early epochs and tightens as the
    system accumulates semantic mass — enforcing conservatism
    in proportion to how much meaning has been accumulated.
    """

    def __init__(
        self,
        initial: float = DEFAULT_LAMBDA_INITIAL,
        decay: float   = DEFAULT_LAMBDA_DECAY,
        minimum: float = DEFAULT_LAMBDA_MIN,
    ) -> None:
        self._lambda = initial
        self._decay  = decay
        self._minimum = minimum
        self._epoch: int = 0

    def tick(self) -> float:
        """Advance one epoch and return the new λ(t)."""
        self._epoch += 1
        self._lambda = max(self._minimum, self._lambda - self._decay)
        return self._lambda

    @property
    def value(self) -> float:
        return self._lambda

    @property
    def epoch(self) -> int:
        return self._epoch

    def __repr__(self) -> str:
        return f"λ(t)={self._lambda:.4f}  epoch={self._epoch}"


# ── Immutable Semantic Container ──────────────────────────────────────────────

@dataclass(frozen=True)
class ImmutableSemanticContainer:
    """
    ISC: The fundamental unit of deep-time information packaging.

    Fields
    ------
    container_id    Unique identifier for this container.
    raw_seed        The original raw data payload (bytes or text).
    delta           Change record relative to a parent container.
    model_snapshot  Serialised model state at the time of creation.
    execution_proof Deterministic proof of correct generation
                    (hash of seed + model_snapshot + delta).
    parent_id       Reference to the parent ISC (None for root containers).
    substrate_tag   Label of the physical/computational substrate at creation.
    created_at      Unix timestamp of creation.
    """
    container_id:    str
    raw_seed:        str
    delta:           dict[str, Any]
    model_snapshot:  str
    execution_proof: str
    parent_id:       Optional[str]
    substrate_tag:   str
    created_at:      float

    @classmethod
    def create(
        cls,
        raw_seed: str,
        delta: dict[str, Any],
        model_snapshot: str,
        parent_id: Optional[str] = None,
        substrate_tag: str = "default",
    ) -> "ImmutableSemanticContainer":
        """Factory: create and cryptographically seal a new ISC."""
        container_id = str(uuid.uuid4())
        created_at   = time.time()

        proof_material = json.dumps(
            {"seed": raw_seed, "model": model_snapshot, "delta": delta},
            sort_keys=True,
        ).encode()
        execution_proof = hashlib.sha256(proof_material).hexdigest()

        return cls(
            container_id=container_id,
            raw_seed=raw_seed,
            delta=delta,
            model_snapshot=model_snapshot,
            execution_proof=execution_proof,
            parent_id=parent_id,
            substrate_tag=substrate_tag,
            created_at=created_at,
        )

    def verify(self) -> bool:
        """Re-derive the execution proof and confirm integrity."""
        proof_material = json.dumps(
            {"seed": self.raw_seed, "model": self.model_snapshot, "delta": self.delta},
            sort_keys=True,
        ).encode()
        expected = hashlib.sha256(proof_material).hexdigest()
        return expected == self.execution_proof

    def __repr__(self) -> str:
        valid = "✅" if self.verify() else "❌"
        return (
            f"ISC[{self.container_id[:8]}]  {valid}  "
            f"parent={self.parent_id[:8] if self.parent_id else 'root'}  "
            f"substrate={self.substrate_tag}"
        )


# ── Coherence & Identity Engine ───────────────────────────────────────────────

class CoherenceIdentityEngine:
    """
    Layer -1: Coherence & Identity Engine.

    Tracks identity drift across epochs, enforces the plasticity budget,
    and manages the ISC lineage chain.

    Usage
    -----
    >>> engine = CoherenceIdentityEngine()
    >>> v0 = IdentityVector({"semantic_mass": 0.5, "novelty": 0.8})
    >>> engine.set_identity(v0)
    >>> v1 = IdentityVector({"semantic_mass": 0.52, "novelty": 0.78})
    >>> engine.update_identity(v1)
    """

    def __init__(
        self,
        lambda_initial: float = DEFAULT_LAMBDA_INITIAL,
        lambda_decay:   float = DEFAULT_LAMBDA_DECAY,
        lambda_min:     float = DEFAULT_LAMBDA_MIN,
    ) -> None:
        self._budget   = PlasticityBudget(lambda_initial, lambda_decay, lambda_min)
        self._identity: Optional[IdentityVector] = None
        self._isc_chain: list[ImmutableSemanticContainer] = []
        self._drift_history: list[float] = []
        self._meaning_rot_events: int = 0

    # ── Identity Management ────────────────────────────────────────────────────

    def set_identity(self, vector: IdentityVector) -> None:
        """Initialise the identity manifold with a root vector."""
        vector.version = 0
        self._identity = vector
        logger.info("⚓ Identity manifold initialised: %s", vector)

    def update_identity(self, new_vector: IdentityVector) -> bool:
        """
        Propose an identity update.
        Accepted if the distance from current identity ≤ λ(t).
        Returns True if accepted, False if rejected (budget exceeded).
        """
        if self._identity is None:
            raise RuntimeError("Identity not initialised. Call set_identity() first.")

        drift = self._identity.distance(new_vector)
        lambda_t = self._budget.tick()
        self._drift_history.append(drift)

        if drift > lambda_t:
            logger.warning(
                "🚫 Identity update REJECTED  drift=%.4f > λ(t)=%.4f  "
                "Semantic change exceeds plasticity budget.",
                drift, lambda_t
            )
            return False

        # Check for Meaning Rot
        if drift > MEANING_ROT_THRESHOLD:
            self._meaning_rot_events += 1
            logger.error(
                "🧬 MEANING ROT DETECTED  drift=%.4f  event #%d",
                drift, self._meaning_rot_events
            )

        new_vector.version = self._identity.version + 1
        new_vector.timestamp = time.time()
        self._identity = new_vector

        logger.debug(
            "✅ Identity updated to v%d  drift=%.4f  λ(t)=%.4f",
            new_vector.version, drift, lambda_t
        )
        return True

    # ── ISC Lineage Chain ──────────────────────────────────────────────────────

    def package(
        self,
        raw_seed: str,
        delta: dict[str, Any],
        model_snapshot: str,
        substrate_tag: str = "default",
    ) -> ImmutableSemanticContainer:
        """
        Package data into a new Immutable Semantic Container and
        append it to the lineage chain.
        """
        parent_id = self._isc_chain[-1].container_id if self._isc_chain else None
        isc = ImmutableSemanticContainer.create(
            raw_seed=raw_seed,
            delta=delta,
            model_snapshot=model_snapshot,
            parent_id=parent_id,
            substrate_tag=substrate_tag,
        )
        self._isc_chain.append(isc)
        logger.debug("📦 Packaged ISC: %s", isc)
        return isc

    def verify_chain(self) -> bool:
        """Verify the integrity of every ISC in the lineage chain."""
        all_valid = all(isc.verify() for isc in self._isc_chain)
        if all_valid:
            logger.info("✅ ISC chain integrity verified (%d containers).", len(self._isc_chain))
        else:
            logger.error("❌ ISC chain integrity FAILURE.")
        return all_valid

    # ── Fossilisation ──────────────────────────────────────────────────────────

    def fossilise(self) -> dict:
        """
        Model Fossilisation: create a permanent read-only snapshot
        of the current identity and ISC chain for long-term archival.
        """
        fossil = {
            "fossilised_at": time.time(),
            "identity_version": self._identity.version if self._identity else None,
            "identity_features": self._identity.features if self._identity else {},
            "isc_count": len(self._isc_chain),
            "chain_valid": self.verify_chain(),
            "plasticity_epoch": self._budget.epoch,
            "lambda_final": self._budget.value,
            "meaning_rot_events": self._meaning_rot_events,
        }
        logger.info("🧬 Identity fossilised at epoch %d.", self._budget.epoch)
        return fossil

    # ── Utilities ──────────────────────────────────────────────────────────────

    @property
    def current_identity(self) -> Optional[IdentityVector]:
        return self._identity

    @property
    def plasticity_budget(self) -> PlasticityBudget:
        return self._budget

    def mean_drift(self) -> float:
        if not self._drift_history:
            return 0.0
        return sum(self._drift_history) / len(self._drift_history)

    def status(self) -> dict:
        return {
            "layer": -1,
            "name": "Coherence & Identity Engine",
            "identity_version": self._identity.version if self._identity else None,
            "lambda_t": self._budget.value,
            "epoch": self._budget.epoch,
            "mean_drift": self.mean_drift(),
            "isc_chain_length": len(self._isc_chain),
            "chain_integrity": self.verify_chain() if self._isc_chain else None,
            "meaning_rot_events": self._meaning_rot_events,
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    engine = CoherenceIdentityEngine()

    v0 = IdentityVector({"semantic_mass": 0.50, "novelty": 0.80, "coherence": 0.90})
    engine.set_identity(v0)

    # Small drift — accepted
    v1 = IdentityVector({"semantic_mass": 0.52, "novelty": 0.78, "coherence": 0.91})
    engine.update_identity(v1)

    # Large drift — rejected
    v2 = IdentityVector({"semantic_mass": 0.95, "novelty": 0.10, "coherence": 0.20})
    engine.update_identity(v2)

    isc = engine.package(
        raw_seed="Cosmic horizon event 4471",
        delta={"delta_type": "observation", "magnitude": 0.02},
        model_snapshot="snapshot_v1_hash_abc123",
    )
    print(isc)
    print(engine.status())
    print(engine.fossilise())
