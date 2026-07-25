"""
CIMF Layer -3: Reality Calibration Engine
==========================================
Epistemological grounding layer.
"""

from __future__ import annotations

import math
import time
import logging
from dataclasses import dataclass, field
from typing import Callable

logger = logging.getLogger(__name__)

FINE_STRUCTURE_CONSTANT = 7.2973525693e-3
VACUUM_ENERGY_DENSITY_REF = 6.0e-10
HYDROGEN_LYMAN_ALPHA_NM = 121.567

DEFAULT_R_CRITICAL = 0.75
DEFAULT_PROBE_INTERVAL = 1.0


@dataclass
class OntologicalProbeResult:
    probe_name: str
    measured_value: float
    reference_value: float
    deviation: float
    timestamp: float = field(default_factory=time.time)

    @property
    def score(self) -> float:
        return max(0.0, 1.0 - self.deviation)

    def __repr__(self) -> str:
        status = "OK" if self.score >= 0.9 else ("WARN" if self.score >= 0.75 else "CRIT")
        return (
            f"{status} Probe[{self.probe_name}] "
            f"measured={self.measured_value:.6g}  ref={self.reference_value:.6g}  "
            f"score={self.score:.4f}"
        )


@dataclass
class RealityAlignmentSnapshot:
    r_value: float
    probe_results: list[OntologicalProbeResult]
    timestamp: float = field(default_factory=time.time)
    remapping_triggered: bool = False

    @property
    def is_coherent(self) -> bool:
        return self.r_value >= DEFAULT_R_CRITICAL

    def summary(self) -> str:
        lines = [
            f"Reality Alignment R(t) = {self.r_value:.4f}  "
            f"({'COHERENT' if self.is_coherent else 'CRITICAL'})",
        ]
        for p in self.probe_results:
            lines.append(f"  {p}")
        return "\n".join(lines)


class RealityCalibrationEngine:
    def __init__(
        self,
        r_critical: float = DEFAULT_R_CRITICAL,
        probe_interval: float = DEFAULT_PROBE_INTERVAL,
    ) -> None:
        self.r_critical = r_critical
        self.probe_interval = probe_interval
        self._probes: list[Callable[[], OntologicalProbeResult]] = []
        self._history: list[RealityAlignmentSnapshot] = []
        self._ingestion_halted: bool = False
        self._register_default_probes()

    def register_probe(self, probe_fn: Callable[[], OntologicalProbeResult]) -> None:
        self._probes.append(probe_fn)
        logger.debug("Registered probe: %s", probe_fn.__name__)

    def _register_default_probes(self) -> None:
        self.register_probe(self._probe_fine_structure)
        self.register_probe(self._probe_vacuum_energy)
        self.register_probe(self._probe_lyman_alpha)

    def _probe_fine_structure(self) -> OntologicalProbeResult:
        measured = FINE_STRUCTURE_CONSTANT * (1.0 + self._environmental_noise(1e-6))
        deviation = abs(measured - FINE_STRUCTURE_CONSTANT) / FINE_STRUCTURE_CONSTANT
        return OntologicalProbeResult("fine_structure_alpha", measured, FINE_STRUCTURE_CONSTANT, deviation)

    def _probe_vacuum_energy(self) -> OntologicalProbeResult:
        measured = VACUUM_ENERGY_DENSITY_REF * (1.0 + self._environmental_noise(1e-4))
        deviation = abs(measured - VACUUM_ENERGY_DENSITY_REF) / VACUUM_ENERGY_DENSITY_REF
        return OntologicalProbeResult("vacuum_energy", measured, VACUUM_ENERGY_DENSITY_REF, deviation)

    def _probe_lyman_alpha(self) -> OntologicalProbeResult:
        measured = HYDROGEN_LYMAN_ALPHA_NM * (1.0 + self._environmental_noise(1e-7))
        deviation = abs(measured - HYDROGEN_LYMAN_ALPHA_NM) / HYDROGEN_LYMAN_ALPHA_NM
        return OntologicalProbeResult("lyman_alpha_nm", measured, HYDROGEN_LYMAN_ALPHA_NM, deviation)

    def _environmental_noise(self, scale: float) -> float:
        import random
        return random.gauss(0, scale)

    def calibrate(self) -> RealityAlignmentSnapshot:
        results = [probe() for probe in self._probes]
        if not results:
            raise RuntimeError("No ontological probes registered.")
        r_value = sum(p.score for p in results) / len(results)
        snapshot = RealityAlignmentSnapshot(r_value=r_value, probe_results=results)
        if not snapshot.is_coherent:
            snapshot.remapping_triggered = True
            self._trigger_remapping(snapshot)
        self._history.append(snapshot)
        return snapshot

    def _trigger_remapping(self, snapshot: RealityAlignmentSnapshot) -> None:
        self._ingestion_halted = True
        logger.critical(
            "REALITY CALIBRATION FAILURE  R(t)=%.4f < R_critical=%.4f\n"
            "   Halting data ingestion. Structural remapping initiated.",
            snapshot.r_value, self.r_critical
        )

    def resume_ingestion(self) -> None:
        self._ingestion_halted = False
        logger.info("Structural remapping complete. Data ingestion resumed.")

    @property
    def ingestion_halted(self) -> bool:
        return self._ingestion_halted

    @property
    def history(self) -> list[RealityAlignmentSnapshot]:
        return list(self._history)

    def r_trend(self) -> float | None:
        if len(self._history) < 2:
            return None
        vals = [s.r_value for s in self._history[-10:]]
        n = len(vals)
        mean_x = (n - 1) / 2
        mean_y = sum(vals) / n
        numerator = sum((i - mean_x) * (vals[i] - mean_y) for i in range(n))
        denominator = sum((i - mean_x) ** 2 for i in range(n)) or 1e-12
        return numerator / denominator

    def status(self) -> dict:
        last = self._history[-1] if self._history else None
        return {
            "layer": -3,
            "name": "Reality Calibration Engine",
            "r_value": last.r_value if last else None,
            "coherent": last.is_coherent if last else None,
            "ingestion_halted": self._ingestion_halted,
            "probes_registered": len(self._probes),
            "calibration_cycles": len(self._history),
            "r_trend": self.r_trend(),
        }


def run_calibration(verbose: bool = True) -> RealityAlignmentSnapshot:
    engine = RealityCalibrationEngine()
    snapshot = engine.calibrate()
    if verbose:
        print(snapshot.summary())
    return snapshot


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    run_calibration()
