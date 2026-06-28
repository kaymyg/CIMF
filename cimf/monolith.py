"""
CIMF Monolith: The Cryptographic Monolith (Post-Darkening Primitive)
=====================================================================
When cosmological horizon expansion causes R(t) → uncomputable,
the active HPM v5 hierarchy collapses to its absolute minimum:

                    THE TOPOLOGICAL CRYSTAL

A passive, zero-power, ground-state crystalline lattice that:

    1. Deactivates all active logic and Landauer-limiting loops
    2. Encodes information as multi-dimensional physical deformations
       within a high-bond-energy lattice (e.g. synthetic diamond)
    3. Strips generative compression and back-converts meaning into
       primitive self-describing logical constants interpretable from
       first principles (The Rosetta Self-Description)
    4. Matches structural state to background temperature T→0 to
       optimise physical decay timescale across geological epochs
       (Engineered Half-Life)

The architecture completes its cycle: from passive matter,
expanding into a living thermodynamic network, then gracefully
consolidating back into a silent, self-contained crystal monument.
"""

from __future__ import annotations

import time
import math
import json
import hashlib
import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Any

logger = logging.getLogger(__name__)


# ── Constants ─────────────────────────────────────────────────────────────────

# Physical anchors for the Rosetta Self-Description
ROSETTA_CONSTANTS = {
    "hydrogen_proton_mass_ratio": 1836.15267343,    # m_p / m_e
    "fine_structure_constant":    7.2973525693e-3,  # α
    "pi":                         math.pi,
    "euler_number":               math.e,
    "golden_ratio":               (1 + math.sqrt(5)) / 2,
    "atomic_number_carbon":       6,                # C — diamond lattice basis
    "bond_energy_diamond_eV":     3.68,             # C–C bond in diamond (eV)
}

# Synthetic diamond lattice parameters
DIAMOND_LATTICE_CONSTANT_NM     = 0.3567          # a = 3.567 Å
DIAMOND_DEBYE_TEMPERATURE_K     = 2230.0           # θ_D for phonon stability
DIAMOND_MELTING_POINT_K         = 3820.0           # Upper thermal bound

# Engineered decay parameters
COSMIC_BACKGROUND_TEMP_TARGET   = 2.725e-30       # Approaching 0 K asymptote
HALF_LIFE_OPTIMISATION_EXPONENT = 2.3             # Empirical crystal longevity factor


# ── Darkening State ───────────────────────────────────────────────────────────

class DarkeningPhase(Enum):
    PRE_DARKENING  = auto()   # Active HPM v5 running
    TRANSITIONING  = auto()   # Preparing for monolith collapse
    POST_DARKENING = auto()   # Monolith is the sole surviving artifact


# ── Rosetta Self-Description ──────────────────────────────────────────────────

@dataclass(frozen=True)
class RosettaBlock:
    """
    A self-describing block of meaning, encoded in physical invariants.

    Rather than relying on any assumed shared language or encoding,
    each block defines its meaning using:
        - Atomic ratios observable from first principles
        - Fundamental physical relationships
        - Geometric series and mathematical constants

    Any sufficiently advanced observer can reconstruct meaning
    without prior knowledge of the encoding system.
    """
    block_id:       str
    semantic_label: str              # Human-readable label (for pre-darkening reference)
    physical_anchors: dict[str, Any] # Invariant physical quantities used as anchors
    geometric_series: list[float]    # e.g. [1, 2, 3, 5, 8, 13, ...] for Fibonacci
    atomic_ratios:    dict[str, float]   # Element ratios defining the lattice structure
    logical_constants: list[str]     # Self-evident truths: "0", "1", "+", "succ"
    integrity_hash:   str            # SHA-256 of the serialised content

    @classmethod
    def encode(
        cls,
        semantic_label: str,
        payload: dict[str, Any],
    ) -> "RosettaBlock":
        """
        Encode a payload as a Rosetta block using physical and mathematical anchors.
        """
        block_id = hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode()
        ).hexdigest()[:12]

        # Embed content meaning within physical invariants
        physical_anchors = dict(ROSETTA_CONSTANTS)
        physical_anchors["payload_summary"] = payload

        # Fibonacci geometric series as a universal mathematical marker
        fib = [1.0, 1.0]
        for _ in range(12):
            fib.append(fib[-1] + fib[-2])

        # Simple atomic ratios (C:H:N) as a chemical anchor
        atomic_ratios = {
            "C:C": 1.0,       # Diamond lattice homogeneous
            "C:N": 0.001,     # Nitrogen vacancy defect doping
            "C:B": 0.0001,    # Boron doping for structural encoding
        }

        logical_constants = ["0", "1", "succ", "+", "×", "=", "∀", "∃"]

        content = {
            "block_id": block_id,
            "physical_anchors": {k: str(v) for k, v in physical_anchors.items()},
            "geometric_series": fib,
            "atomic_ratios": atomic_ratios,
            "logical_constants": logical_constants,
        }
        integrity_hash = hashlib.sha256(
            json.dumps(content, sort_keys=True).encode()
        ).hexdigest()

        return cls(
            block_id=block_id,
            semantic_label=semantic_label,
            physical_anchors=physical_anchors,
            geometric_series=fib,
            atomic_ratios=atomic_ratios,
            logical_constants=logical_constants,
            integrity_hash=integrity_hash,
        )

    def verify(self) -> bool:
        content = {
            "block_id": self.block_id,
            "physical_anchors": {k: str(v) for k, v in self.physical_anchors.items()},
            "geometric_series": self.geometric_series,
            "atomic_ratios": self.atomic_ratios,
            "logical_constants": self.logical_constants,
        }
        expected = hashlib.sha256(
            json.dumps(content, sort_keys=True).encode()
        ).hexdigest()
        return expected == self.integrity_hash

    def __repr__(self) -> str:
        valid = "✅" if self.verify() else "❌"
        return (
            f"RosettaBlock[{self.block_id}] {valid}  "
            f"'{self.semantic_label}'  anchors={len(self.physical_anchors)}"
        )


# ── Diamond Lattice Encoder ───────────────────────────────────────────────────

@dataclass
class LatticeDeformation:
    """
    Represents a physical deformation within the diamond crystal lattice
    used to encode information as a stable geometric distortion.
    """
    site_index:      tuple[int, int, int]   # (x, y, z) lattice site
    deformation_nm:  float                  # displacement from equilibrium (nm)
    dopant:          Optional[str] = None   # N, B, or None for vacancies
    bond_angle_deg:  float = 109.5          # Tetrahedral angle; deviation encodes data

    @property
    def encoded_bit(self) -> int:
        """Extract a logical bit from the bond angle deviation."""
        deviation = abs(self.bond_angle_deg - 109.5)
        return 1 if deviation > 0.5 else 0


class DiamondLatticeEncoder:
    """
    Encodes information as multi-dimensional deformations within a
    synthetic diamond lattice. Leverages the extreme bond strength
    (3.68 eV per C–C bond) and Debye temperature (2230 K) for
    passive quantum stability across deep time.
    """

    def __init__(self, lattice_size: int = 16) -> None:
        """lattice_size: number of unit cells per dimension (N×N×N grid)."""
        self.lattice_size = lattice_size
        self._sites: dict[tuple, LatticeDeformation] = {}

    def encode_bytes(self, data: bytes) -> int:
        """
        Map a byte sequence into lattice deformations.
        Returns the number of lattice sites written.
        """
        bits = "".join(f"{byte:08b}" for byte in data)
        sites_written = 0

        for idx, bit in enumerate(bits):
            if idx >= self.lattice_size ** 3:
                logger.warning("Lattice capacity exceeded at bit %d; truncating.", idx)
                break

            x = idx % self.lattice_size
            y = (idx // self.lattice_size) % self.lattice_size
            z = idx // (self.lattice_size ** 2)

            angle = 110.0 if bit == "1" else 109.5
            deform = LatticeDeformation(
                site_index=(x, y, z),
                deformation_nm=0.001 * (1 if bit == "1" else 0),
                bond_angle_deg=angle,
            )
            self._sites[(x, y, z)] = deform
            sites_written += 1

        return sites_written

    def decode_bytes(self, n_bytes: int) -> bytes:
        """Recover bytes from lattice deformations."""
        bits = []
        for idx in range(n_bytes * 8):
            x = idx % self.lattice_size
            y = (idx // self.lattice_size) % self.lattice_size
            z = idx // (self.lattice_size ** 2)
            site = self._sites.get((x, y, z))
            bits.append(str(site.encoded_bit) if site else "0")

        result = bytearray()
        for i in range(0, len(bits) - 7, 8):
            byte = int("".join(bits[i:i+8]), 2)
            result.append(byte)
        return bytes(result)

    @property
    def capacity_bytes(self) -> int:
        return (self.lattice_size ** 3) // 8

    def status(self) -> dict:
        return {
            "lattice_size": self.lattice_size,
            "capacity_bytes": self.capacity_bytes,
            "sites_written": len(self._sites),
            "fill_fraction": len(self._sites) / (self.lattice_size ** 3),
            "lattice_constant_nm": DIAMOND_LATTICE_CONSTANT_NM,
            "debye_temperature_K": DIAMOND_DEBYE_TEMPERATURE_K,
        }


# ── Engineered Half-Life ──────────────────────────────────────────────────────

def engineered_half_life(
    background_temp_k: float = COSMIC_BACKGROUND_TEMP_TARGET,
    bond_energy_ev: float = 3.68,
    exponent: float = HALF_LIFE_OPTIMISATION_EXPONENT,
) -> float:
    """
    Estimate the engineered half-life of the crystal monolith (in years).

    As the universe cools toward T→0, thermal phonon excitations approach
    zero. The dominant decay mechanism shifts to quantum tunnelling, which
    is suppressed by the high bond energy. Half-life grows as:

        τ₁/₂ ∝ exp( E_bond / (k_B × T) )^exponent

    At T→0, τ₁/₂ → ∞ in the ideal limit.
    """
    k_B_eV_per_K = 8.617333e-5   # Boltzmann constant in eV/K
    t_eff = max(background_temp_k, 1e-30)  # Guard against exact zero
    exponent_arg = bond_energy_ev / (k_B_eV_per_K * t_eff)
    # Clamp to avoid overflow in float
    log_tau = min(exponent * exponent_arg, 700)
    tau_seconds = math.exp(log_tau)
    SECONDS_PER_YEAR = 3.156e7
    return tau_seconds / SECONDS_PER_YEAR


# ── Cryptographic Monolith ────────────────────────────────────────────────────

class CryptographicMonolith:
    """
    The Topological Crystal — passive zero-power information monument.

    Constructed by the HPM v5 system during the Epistemic Darkening
    transition. Once sealed, it is inert and requires no active maintenance,
    power, or external environment to preserve its encoded meaning.

    Usage
    -----
    >>> monolith = CryptographicMonolith()
    >>> monolith.load_from_active_system({"epoch": 4471, "core_knowledge": "..."})
    >>> monolith.seal()
    >>> print(monolith.status())
    """

    def __init__(self, lattice_size: int = 32) -> None:
        self._phase      = DarkeningPhase.PRE_DARKENING
        self._sealed     = False
        self._encoder    = DiamondLatticeEncoder(lattice_size=lattice_size)
        self._rosetta_blocks: list[RosettaBlock] = []
        self._sealed_at: Optional[float] = None
        self._half_life_years: Optional[float] = None

    # ── Loading ────────────────────────────────────────────────────────────────

    def load_from_active_system(self, knowledge: dict[str, Any]) -> None:
        """
        Ingest knowledge from the active HPM v5 system for crystallisation.
        Must be called before seal().
        """
        if self._sealed:
            raise RuntimeError("Monolith is sealed; cannot load new data.")
        self._phase = DarkeningPhase.TRANSITIONING

        # Encode payload into the diamond lattice
        payload_bytes = json.dumps(knowledge, sort_keys=True).encode()
        sites = self._encoder.encode_bytes(payload_bytes)
        logger.info("⟡ Lattice encoded %d sites from active system payload.", sites)

        # Build Rosetta blocks for each top-level knowledge category
        for key, value in knowledge.items():
            block = RosettaBlock.encode(
                semantic_label=key,
                payload={key: value},
            )
            self._rosetta_blocks.append(block)
            logger.debug("  Rosetta block: %s", block)

    def seal(self, background_temp_k: float = COSMIC_BACKGROUND_TEMP_TARGET) -> None:
        """
        Seal the monolith: deactivate all active logic and transition to
        passive ground-state preservation. This action is irreversible.
        """
        if self._sealed:
            raise RuntimeError("Monolith is already sealed.")
        if self._phase != DarkeningPhase.TRANSITIONING:
            raise RuntimeError(
                "Must call load_from_active_system() before seal()."
            )

        # Verify all Rosetta blocks before sealing
        invalid = [b for b in self._rosetta_blocks if not b.verify()]
        if invalid:
            raise ValueError(
                f"{len(invalid)} Rosetta block(s) failed integrity check. Aborting seal."
            )

        self._sealed    = True
        self._sealed_at = time.time()
        self._phase     = DarkeningPhase.POST_DARKENING
        self._half_life_years = engineered_half_life(background_temp_k)

        logger.info(
            "🔮 MONOLITH SEALED  Rosetta blocks=%d  Lattice sites=%d  "
            "Engineered half-life=%.3e years",
            len(self._rosetta_blocks),
            self._encoder.status()["sites_written"],
            self._half_life_years,
        )

    # ── Read-Only Access ───────────────────────────────────────────────────────

    def inspect_rosetta(self) -> list[str]:
        """Return a human-readable summary of all Rosetta blocks."""
        return [str(b) for b in self._rosetta_blocks]

    def verify_integrity(self) -> bool:
        """Verify all Rosetta blocks are still intact."""
        return all(b.verify() for b in self._rosetta_blocks)

    # ── Status ─────────────────────────────────────────────────────────────────

    def status(self) -> dict:
        return {
            "component": "Cryptographic Monolith",
            "phase": self._phase.name,
            "sealed": self._sealed,
            "sealed_at": self._sealed_at,
            "rosetta_blocks": len(self._rosetta_blocks),
            "lattice": self._encoder.status(),
            "integrity_intact": self.verify_integrity() if self._sealed else None,
            "half_life_years": self._half_life_years,
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    monolith = CryptographicMonolith(lattice_size=16)

    # Simulate loading the HPM v5 system's final knowledge state
    final_knowledge = {
        "cosmological_epoch": 4471,
        "unified_invariant":  "Survival = Stability × Coherence × Grounding × Action",
        "last_r_value":       0.94,
        "phi_final":          0.88,
        "core_axioms":        ["causality", "conservation", "symmetry"],
        "civilisation_record": "Encoded in diamond lattice site deformations.",
    }

    monolith.load_from_active_system(final_knowledge)
    monolith.seal(background_temp_k=2.725e-10)

    print("\nRosetta blocks:")
    for line in monolith.inspect_rosetta():
        print(" ", line)

    print("\nMonolith status:")
    import json
    print(json.dumps(monolith.status(), indent=2, default=str))
