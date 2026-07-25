"""CIMF Layer -1: Coherence & Identity Engine"""

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

DEFAULT_LAMBDA_INITIAL = 0.10
DEFAULT_LAMBDA_DECAY = 0.005
DEFAULT_LAMBDA_MIN = 0.005
MEANING_ROT_THRESHOLD = 0.30


@dataclass
class IdentityVector:
    features: dict[str, float]
    version: int = 0
    timestamp: float = field(default_factory=time.time)

    def distance(self, other: "IdentityVector") -> float:
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


class PlasticityBudget:
    def __init__(self, initial=DEFAULT_LAMBDA_INITIAL, decay=DEFAULT_LAMBDA_DECAY, minimum=DEFAULT_LAMBDA_MIN) -> None:
        self._lambda = initial
        self._decay = decay
        self._minimum = minimum
        self._epoch: int = 0

    def tick(self) -> float:
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
        return f"lambda(t)={self._lambda:.4f}  epoch={self._epoch}"


@dataclass(frozen=True)
class ImmutableSemanticContainer:
    container_id: str
    raw_seed: str
    delta: dict[str, Any]
    model_snapshot: str
    execution_proof: str
    parent_id: Optional[str]
    substrate_tag: str
    created_at: float

    @classmethod
    def create(cls, raw_seed, delta, model_snapshot, parent_id=None, substrate_tag="default"):
        container_id = str(uuid.uuid4())
        created_at = time.time()
        proof_material = json.dumps(
            {"seed": raw_seed, "model": model_snapshot, "delta": delta}, sort_keys=True
        ).encode()
        execution_proof = hashlib.sha256(proof_material).hexdigest()
        return cls(container_id, raw_seed, delta, model_snapshot, execution_proof,
                   parent_id, substrate_tag, created_at)

    def verify(self) -> bool:
        proof_material = json.dumps(
            {"seed": self.raw_seed, "model": self.model_snapshot, "delta": self.delta}, sort_keys=True
        ).encode()
        return hashlib.sha256(proof_material).hexdigest() == self.execution_proof

    def __repr__(self) -> str:
        valid = "OK" if self.verify() else "FAIL"
        return (f"ISC[{self.container_id[:8]}]  {valid}  "
                f"parent={self.parent_id[:8] if self.parent_id else 'root'}  "
                f"substrate={self.substrate_tag}")


class CoherenceIdentityEngine:
    def __init__(self, lambda_initial=DEFAULT_LAMBDA_INITIAL, lambda_decay=DEFAULT_LAMBDA_DECAY, lambda_min=DEFAULT_LAMBDA_MIN) -> None:
        self._budget = PlasticityBudget(lambda_initial, lambda_decay, lambda_min)
        self._identity: Optional[IdentityVector] = None
        self._isc_chain: list[ImmutableSemanticContainer] = []
        self._drift_history: list[float] = []
        self._meaning_rot_events: int = 0

    def set_identity(self, vector: IdentityVector) -> None:
        vector.version = 0
        self._identity = vector
        logger.info("Identity manifold initialised: %s", vector)

    def update_identity(self, new_vector: IdentityVector) -> bool:
        if self._identity is None:
            raise RuntimeError("Identity not initialised. Call set_identity() first.")
        drift = self._identity.distance(new_vector)
        lambda_t = self._budget.tick()
        self._drift_history.append(drift)
        if drift > lambda_t:
            logger.warning("Identity update REJECTED  drift=%.4f > lambda(t)=%.4f", drift, lambda_t)
            return False
        if drift > MEANING_ROT_THRESHOLD:
            self._meaning_rot_events += 1
            logger.error("MEANING ROT DETECTED  drift=%.4f  event #%d", drift, self._meaning_rot_events)
        new_vector.version = self._identity.version + 1
        new_vector.timestamp = time.time()
        self._identity = new_vector
        logger.debug("Identity updated to v%d  drift=%.4f  lambda(t)=%.4f", new_vector.version, drift, lambda_t)
        return True

    def package(self, raw_seed, delta, model_snapshot, substrate_tag="default"):
        parent_id = self._isc_chain[-1].container_id if self._isc_chain else None
        isc = ImmutableSemanticContainer.create(raw_seed, delta, model_snapshot, parent_id, substrate_tag)
        self._isc_chain.append(isc)
        logger.debug("Packaged ISC: %s", isc)
        return isc

    def verify_chain(self) -> bool:
        all_valid = all(isc.verify() for isc in self._isc_chain)
        if all_valid:
            logger.info("ISC chain integrity verified (%d containers).", len(self._isc_chain))
        else:
            logger.error("ISC chain integrity FAILURE.")
        return all_valid

    def fossilise(self) -> dict:
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
        logger.info("Identity fossilised at epoch %d.", self._budget.epoch)
        return fossil

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
    v1 = IdentityVector({"semantic_mass": 0.52, "novelty": 0.78, "coherence": 0.91})
    engine.update_identity(v1)
    v2 = IdentityVector({"semantic_mass": 0.95, "novelty": 0.10, "coherence": 0.20})
    engine.update_identity(v2)
    isc = engine.package("Cosmic horizon event 4471", {"delta_type": "observation", "magnitude": 0.02}, "snapshot_v1_hash_abc123")
    print(isc)
    print(engine.status())
    print(engine.fossilise())
