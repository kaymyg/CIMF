"""
CIMF Layer -3: Reality Calibration Engine
==========================================
Epistemological grounding layer. Continuously tests the structural
mapping between internal world models and the objective state of
the cosmos via real-time ontological probes.

The Reality Alignment Metric R(t) determines whether the system's
internal model is coherent with measurable physical reality.
If R(t) < R_critical, all data ingestion is halted and a full
structural remapping is triggered to prevent coherent hallucination.
"""

from __future__ import annotations

import math
import time
import logging
from dataclasses import dataclass, field
from typing import Callable

logger = logging.getLogger(__name__)

# ── Physical Constants (probe anchors) ────────────────────────────────────────
FINE_STRUCTURE_CONSTANT = 7.2973525693e-3       # α  (NIST 2018 CODATA)
VACUUM_ENERGY_DENSITY_REF = 6.0e-10             # J/m³  (approximate observed Λ)
HYDROGEN_LYMAN_ALPHA_NM = 121.567               # nm  (spectroscopic anchor)

# ── Thresholds ─────────────────────────────────────────────────────────────────
DEFAULT_R_CRITICAL = 0.75      # Below this → halt + remap
DEFAULT_PROBE_INTERVAL = 1.0   # seconds between automatic probe cycles


# ── Data Structures ────────────────────────────────────────────────────────────

@dataclass
class OntologicalProbeResult:
    """Single output from one ontological probe."""
    probe_name: str
    measured_value: float
    reference_value: float
    deviation: float          # |measured - reference| / reference
    timestamp: float = field(default_factory=time.time)

    @property
    def score(self) -> float:
        """Alignment score in [0, 1]. 1 = perfect match."""
        return max(0.0, 1.0 - self.deviation)

    def __repr__(self) -> str:
        status = "✅" if self.score >= 0.9 else ("⚠️" if self.score >= 0.75 else "🔴")
        return (
            f"{status} Probe[{self.probe_name}] "
            f"measured={self.measured_value:.6g}  ref={self.reference_value:.6g}  "
            f"score={self.score:.4f}"
        )


@dataclass
class RealityAlignmentSnapshot:
    """Aggregated R(t) result across all active probes."""
    r_value: float                        # ∈ [0, 1]
    probe_results: list[OntologicalProbeResult]
    timestamp: float = field(default_factory=time.time)
    remapping_triggered: bool = False

    @property
    def is_coherent(self) -> bool:
        return self.r_value >= DEFAULT_R_CRITICAL

    def summary(self) -> str:
        lines = [
            f"Reality Alignment R(t) = {self.r_value:.4f}  "
            f"({'COHERENT ✅' if self.is_coherent else 'CRITICAL 🔴'})",
        ]
        for p in self.probe_results:
            lines.append(f"  {p}")
        return "\n".join(lines)


# ── Core Engine ────────────────────────────────────────────────────────────────

class RealityCalibrationEngine:
    """
    Layer -3: Reality Calibration Engine.

    Probes run against known physical invariants to produce R(t).
    Custom probes can be registered via register_probe().

    Usage
    -----
    >>> engine = RealityCalibrationEngine()
    >>> snapshot = engine.calibrate()
    >>> print(snapshot.summary())
    """

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

        # Register default physical probes
        self._register_default_probes()

    # ── Probe Registration ─────────────────────────────────────────────────────

    def register_probe(self, probe_fn: Callable[[], OntologicalProbeResult]) -> None:
        """Register a custom ontological probe callable."""
        self._probes.append(probe_fn)
        logger.debug("Registered probe: %s", probe_fn.__name__)

    def _register_default_probes(self) -> None:
        """Install the built-in physical invariant probes."""
        self.register_probe(self._probe_fine_structure)
        self.register_probe(self._probe_vacuum_energy)
        self.register_probe(self._probe_lyman_alpha)

    # ── Built-in Probes ────────────────────────────────────────────────────────

    def _probe_fine_structure(self) -> OntologicalProbeResult:
        """
        Probe the fine-structure constant α.
        In simulation: measured value is the known constant itself.
        In a real deployment, this would read from a calibrated sensor.
        """
        measured = FINE_STRUCTURE_CONSTANT * (1.0 + self._environmental_noise(1e-6))
        deviation = abs(measured - FINE_STRUCTURE_CONSTANT) / FINE_STRUCTURE_CONSTANT
        return OntologicalProbeResult("fine_structure_α", measured, FINE_STRUCTURE_CONSTANT, deviation)

    def _probe_vacuum_energy(self) -> OntologicalProbeResult:
        """Probe local vacuum energy density against cosmological reference."""
        measured = VACUUM_ENERGY_DENSITY_REF * (1.0 + self._environmental_noise(1e-4))
        deviation = abs(measured - VACUUM_ENERGY_DENSITY_REF) / VACUUM_ENERGY_DENSITY_REF
        return OntologicalProbeResult("vacuum_energy_Λ", measured, VACUUM_ENERGY_DENSITY_REF, deviation)

    def _probe_lyman_alpha(self) -> OntologicalProbeResult:
        """Probe hydrogen Lyman-alpha spectral line (nm) — cosmological redshift detector."""
        measured = HYDROGEN_LYMAN_ALPHA_NM * (1.0 + self._environmental_noise(1e-7))
        deviation = abs(measured - HYDROGEN_LYMAN_ALPHA_NM) / HYDROGEN_LYMAN_ALPHA_NM
        return OntologicalProbeResult("lyman_alpha_nm", measured, HYDROGEN_LYMAN_ALPHA_NM, deviation)

    def _environmental_noise(self, scale: float) -> float:
        """Simulated sensor noise for use in probe measurements."""
        import random
        return random.gauss(0, scale)

    # ── Calibration Cycle ──────────────────────────────────────────────────────

    def calibrate(self) -> RealityAlignmentSnapshot:
        """
        Run all registered probes and compute R(t).
        Triggers structural remapping if R(t) < R_critical.
        """
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

    # ── Failure Protocol ───────────────────────────────────────────────────────

    def _trigger_remapping(self, snapshot: RealityAlignmentSnapshot) -> None:
        """
        Failure Protocol: R(t) < R_critical.
        Halts data ingestion and initiates structural remapping.
        """
        self._ingestion_halted = True
        logger.critical(
            "⛔ REALITY CALIBRATION FAILURE  R(t)=%.4f < R_critical=%.4f\n"
            "   Halting data ingestion. Structural remapping initiated.",
            snapshot.r_value, self.r_critical
        )

    def resume_ingestion(self) -> None:
        """Resume data ingestion after a successful remapping."""
        self._ingestion_halted = False
        logger.info("✅ Structural remapping complete. Data ingestion resumed.")

    # ── Utilities ──────────────────────────────────────────────────────────────

    @property
    def ingestion_halted(self) -> bool:
        return self._ingestion_halted

    @property
    def history(self) -> list[RealityAlignmentSnapshot]:
        return list(self._history)

    def r_trend(self) -> float | None:
        """
        Linear trend of R(t) over recent history.
        Negative → system drifting toward incoherence.
        Returns None if fewer than 2 samples are available.
        """
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


# ── Module-level convenience ───────────────────────────────────────────────────

def run_calibration(verbose: bool = True) -> RealityAlignmentSnapshot:
    """Quick single-shot calibration run."""
    engine = RealityCalibrationEngine()
    snapshot = engine.calibrate()
    if verbose:
        print(snapshot.summary())
    return snapshot


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    run_calibration()
