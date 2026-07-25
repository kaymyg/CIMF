"""CIMF — Cosmological Information Management Framework (HPM v5)"""

from cimf.layer_minus3 import RealityCalibrationEngine, RealityAlignmentSnapshot
from cimf.layer_minus2 import MetaGovernanceEngine, AttractorState, AttractorResult
from cimf.layer_minus1 import CoherenceIdentityEngine, IdentityVector, ImmutableSemanticContainer
from cimf.layer_0      import EntropyGovernanceEngine, WorkloadProfile, Pipeline
from cimf.layers_1_to_3 import PhysicalStorageCore
from cimf.monolith     import CryptographicMonolith, DarkeningPhase

import logging
import time
from typing import Any

logger = logging.getLogger(__name__)

__version__ = "5.0.0"
__author__  = "Sahek"
__all__ = [
    "HPMv5",
    "RealityCalibrationEngine", "RealityAlignmentSnapshot",
    "MetaGovernanceEngine", "AttractorState", "AttractorResult",
    "CoherenceIdentityEngine", "IdentityVector", "ImmutableSemanticContainer",
    "EntropyGovernanceEngine", "WorkloadProfile", "Pipeline",
    "PhysicalStorageCore",
    "CryptographicMonolith", "DarkeningPhase",
]


class HPMv5:
    """HPM v5: Hierarchical Persistence Matrix — Complete Seven-Layer Stack."""

    def __init__(self) -> None:
        logger.info("Initialising HPM v5 — Cosmological Information Management Framework")
        self.l_minus3 = RealityCalibrationEngine()
        self.l_minus2 = MetaGovernanceEngine()
        self.l_minus1 = CoherenceIdentityEngine()
        self.l0       = EntropyGovernanceEngine()
        self.physical = PhysicalStorageCore()
        self._monolith: CryptographicMonolith | None = None
        self._darkened: bool = False
        self._cycle_count: int = 0

        default_identity = IdentityVector({
            "semantic_mass": 0.50, "novelty": 0.70,
            "coherence": 0.80, "adaptability": 0.75,
        })
        self.l_minus1.set_identity(default_identity)
        logger.info("HPM v5 online. All layers initialised.")

    def run_cycle(self, attractor_state=None, identity_update=None, write_data=None) -> dict[str, Any]:
        if self._darkened:
            raise RuntimeError("System has undergone Epistemic Darkening. Only the monolith remains.")

        self._cycle_count += 1
        report: dict[str, Any] = {"cycle": self._cycle_count, "timestamp": time.time()}

        snapshot = self.l_minus3.calibrate()
        report["r_value"] = snapshot.r_value
        report["coherent"] = snapshot.is_coherent

        if not snapshot.is_coherent:
            logger.error("Cycle %d aborted: reality calibration failure.", self._cycle_count)
            report["aborted"] = True
            return report

        if attractor_state is None:
            attractor_state = AttractorState(eta=0.80, A=0.70, G=0.65, C=0.85, R=snapshot.r_value)
        attractor_result = self.l_minus2.evaluate(attractor_state)
        report["phi"] = attractor_result.phi
        report["catatonia_risk"] = attractor_result.catatonia_risk

        if identity_update is not None:
            report["identity_update_accepted"] = self.l_minus1.update_identity(identity_update)

        if write_data is not None:
            profile = WorkloadProfile(
                workload_id=f"cycle_{self._cycle_count}",
                novelty=attractor_result.state.G,
                compressibility=1.0 - attractor_result.state.G,
                query_frequency=attractor_result.state.eta,
                size_bytes=len(write_data),
            )
            triage = self.l0.ingest(profile)
            state_id = self.physical.write(write_data)
            report["triage_pipeline"] = triage.assigned_pipeline.name
            report["state_id"] = state_id

        return report

    def initiate_darkening_transition(self, final_knowledge, background_temp_k=2.725e-10, lattice_size=64):
        logger.warning("INITIATING EPISTEMIC DARKENING TRANSITION  R(t) -> uncomputable.")
        final_knowledge["_cimf_meta"] = {
            "hpm_version": __version__,
            "total_cycles": self._cycle_count,
            "l_minus3_status": self.l_minus3.status(),
            "l_minus1_fossil": self.l_minus1.fossilise(),
            "l0_burden": self.l0.lifetime_burden(),
        }
        monolith = CryptographicMonolith(lattice_size=lattice_size)
        monolith.load_from_active_system(final_knowledge)
        monolith.seal(background_temp_k=background_temp_k)
        self._monolith = monolith
        self._darkened = True
        logger.info("Darkening complete. Monolith sealed. HPM v5 deactivated.")
        return monolith

    def status(self) -> dict[str, Any]:
        if self._darkened:
            return {"state": "POST_DARKENING", "monolith": self._monolith.status() if self._monolith else None}
        return {
            "state": "ACTIVE",
            "version": __version__,
            "cycle_count": self._cycle_count,
            "layers": {
                "L-3": self.l_minus3.status(),
                "L-2": self.l_minus2.status(),
                "L-1": self.l_minus1.status(),
                "L0":  self.l0.status(),
                "L1-3": self.physical.status(),
            },
        }


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO)
    hpm = HPMv5()
    for i in range(3):
        report = hpm.run_cycle(write_data=f"Cosmic observation epoch {i+1}".encode())
        print(f"Cycle {report['cycle']}: Phi={report.get('phi', 'N/A'):.4f}  R={report['r_value']:.4f}")
    print("\nFull system status:")
    print(json.dumps(hpm.status(), indent=2, default=str))
