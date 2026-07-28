"""CIMF Monolith: The Cryptographic Monolith (Post-Darkening Primitive)"""

from __future__ import annotations

import time
import math
import json
import hashlib
import logging
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, Any

logger = logging.getLogger(__name__)

ROSETTA_CONSTANTS = {
    "hydrogen_proton_mass_ratio": 1836.15267343,
    "fine_structure_constant": 7.2973525693e-3,
    "pi": math.pi,
    "euler_number": math.e,
    "golden_ratio": (1 + math.sqrt(5)) / 2,
    "atomic_number_carbon": 6,
    "bond_energy_diamond_eV": 3.68,
}

DIAMOND_LATTICE_CONSTANT_NM = 0.3567
DIAMOND_DEBYE_TEMPERATURE_K = 2230.0
DIAMOND_MELTING_POINT_K = 3820.0

COSMIC_BACKGROUND_TEMP_TARGET = 2.725e-30
HALF_LIFE_OPTIMISATION_EXPONENT = 2.3


class DarkeningPhase(Enum):
    PRE_DARKENING = auto()
    TRANSITIONING = auto()
    POST_DARKENING = auto()


@dataclass(frozen=True)
class RosettaBlock:
    block_id: str
    semantic_label: str
    physical_anchors: dict[str, Any]
    geometric_series: list[float]
    atomic_ratios: dict[str, float]
    logical_constants: list[str]
    integrity_hash: str

    @classmethod
    def encode(cls, semantic_label: str, payload: dict[str, Any]) -> "RosettaBlock":
        block_id = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:12]
        physical_anchors = dict(ROSETTA_CONSTANTS)
        physical_anchors["payload_summary"] = payload
        fib = [1.0, 1.0]
        for _ in range(12):
            fib.append(fib[-1] + fib[-2])
        atomic_ratios = {"C:C": 1.0, "C:N": 0.001, "C:B": 0.0001}
        logical_constants = ["0", "1", "succ", "+", "x", "=", "forall", "exists"]
        content = {
            "block_id": block_id,
            "physical_anchors": {k: str(v) for k, v in physical_anchors.items()},
            "geometric_series": fib,
            "atomic_ratios": atomic_ratios,
            "logical_constants": logical_constants,
        }
        integrity_hash = hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()
        return cls(block_id, semantic_label, physical_anchors, fib, atomic_ratios, logical_constants, integrity_hash)

    def verify(self) -> bool:
        content = {
            "block_id": self.block_id,
            "physical_anchors": {k: str(v) for k, v in self.physical_anchors.items()},
            "geometric_series": self.geometric_series,
            "atomic_ratios": self.atomic_ratios,
            "logical_constants": self.logical_constants,
        }
        expected = hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()
        return expected == self.integrity_hash

    def __repr__(self) -> str:
        valid = "OK" if self.verify() else "FAIL"
        return f"RosettaBlock[{self.block_id}] {valid}  '{self.semantic_label}'  anchors={len(self.physical_anchors)}"


@dataclass
class LatticeDeformation:
    site_index: tuple[int, int, int]
    deformation_nm: float
    dopant: Optional[str] = None
    bond_angle_deg: float = 109.5

    # Decision boundary for reading a bit back out of the lattice. The encoder
    # writes 110.0 for a 1 and 109.5 for a 0, so the threshold belongs at the
    # MIDPOINT (0.25 deviation). The previous value compared `> 0.5` against a
    # deviation that was exactly 0.5, so every 1 bit decoded as 0 and the
    # monolith silently lost 100% of its payload.
    BIT_THRESHOLD_DEG = 0.25

    @property
    def encoded_bit(self) -> int:
        deviation = abs(self.bond_angle_deg - 109.5)
        return 1 if deviation >= self.BIT_THRESHOLD_DEG else 0


class DiamondLatticeEncoder:
    def __init__(self, lattice_size: int = 16) -> None:
        self.lattice_size = lattice_size
        self._sites: dict[tuple, LatticeDeformation] = {}

    def encode_bytes(self, data: bytes) -> int:
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


def engineered_half_life(
    background_temp_k: float = COSMIC_BACKGROUND_TEMP_TARGET,
    bond_energy_ev: float = 3.68,
    exponent: float = HALF_LIFE_OPTIMISATION_EXPONENT,
) -> float:
    k_B_eV_per_K = 8.617333e-5
    t_eff = max(background_temp_k, 1e-30)
    exponent_arg = bond_energy_ev / (k_B_eV_per_K * t_eff)
    log_tau = min(exponent * exponent_arg, 700)
    tau_seconds = math.exp(log_tau)
    SECONDS_PER_YEAR = 3.156e7
    return tau_seconds / SECONDS_PER_YEAR


class CryptographicMonolith:
    def __init__(self, lattice_size: int = 32) -> None:
        self._phase = DarkeningPhase.PRE_DARKENING
        self._sealed = False
        self._encoder = DiamondLatticeEncoder(lattice_size=lattice_size)
        self._rosetta_blocks: list[RosettaBlock] = []
        self._payload_bytes: bytes = b""
        self._sealed_at: Optional[float] = None
        self._half_life_years: Optional[float] = None

    def load_from_active_system(self, knowledge: dict[str, Any]) -> None:
        if self._sealed:
            raise RuntimeError("Monolith is sealed; cannot load new data.")
        self._phase = DarkeningPhase.TRANSITIONING
        payload_bytes = json.dumps(knowledge, sort_keys=True).encode()

        # Sealing is irreversible, so refuse to silently truncate. encode_bytes()
        # previously dropped any overflow with only a log warning, and seal()
        # then reported success on a partially-destroyed archive.
        if len(payload_bytes) > self._encoder.capacity_bytes:
            needed = math.ceil(((len(payload_bytes) * 8) ** (1.0 / 3.0)))
            raise ValueError(
                f"Payload {len(payload_bytes)} bytes exceeds lattice capacity "
                f"{self._encoder.capacity_bytes} bytes "
                f"(lattice_size={self._encoder.lattice_size}). "
                f"Increase lattice_size to at least {needed}."
            )

        self._payload_bytes = payload_bytes
        sites = self._encoder.encode_bytes(payload_bytes)
        logger.info("Lattice encoded %d sites from active system payload.", sites)
        for key, value in knowledge.items():
            block = RosettaBlock.encode(semantic_label=key, payload={key: value})
            self._rosetta_blocks.append(block)
            logger.debug("  Rosetta block: %s", block)

    def seal(self, background_temp_k: float = COSMIC_BACKGROUND_TEMP_TARGET) -> None:
        if self._sealed:
            raise RuntimeError("Monolith is already sealed.")
        if self._phase != DarkeningPhase.TRANSITIONING:
            raise RuntimeError("Must call load_from_active_system() before seal().")
        invalid = [b for b in self._rosetta_blocks if not b.verify()]
        if invalid:
            raise ValueError(f"{len(invalid)} Rosetta block(s) failed integrity check. Aborting seal.")

        # Verify the LATTICE, not just the in-memory Rosetta blocks. Without this
        # the total-data-loss bug in LatticeDeformation.encoded_bit sealed as a
        # clean success, because nothing ever exercised the decode path.
        recovered = self._encoder.decode_bytes(len(self._payload_bytes))
        if recovered != self._payload_bytes:
            raise ValueError(
                "Lattice round-trip verification FAILED. Refusing to seal: "
                "the encoded payload cannot be recovered from the lattice."
            )
        self._sealed = True
        self._sealed_at = time.time()
        self._phase = DarkeningPhase.POST_DARKENING
        self._half_life_years = engineered_half_life(background_temp_k)
        logger.info("MONOLITH SEALED  Rosetta blocks=%d  Lattice sites=%d  Engineered half-life=%.3e years",
                    len(self._rosetta_blocks), self._encoder.status()["sites_written"], self._half_life_years)

    def inspect_rosetta(self) -> list[str]:
        return [str(b) for b in self._rosetta_blocks]

    def verify_integrity(self) -> bool:
        return all(b.verify() for b in self._rosetta_blocks)

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
    final_knowledge = {
        "cosmological_epoch": 4471,
        "unified_invariant": "Survival = Stability x Coherence x Grounding x Action",
        "last_r_value": 0.94,
        "phi_final": 0.88,
        "core_axioms": ["causality", "conservation", "symmetry"],
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
