"""Regression tests for CIMF. Every test here corresponds to a bug that shipped
undetected because the repo had no tests at all."""

import math
import random

import pytest

from cimf import HPMv5
from cimf.monolith import (
    CryptographicMonolith, DiamondLatticeEncoder, LatticeDeformation, RosettaBlock,
)
from cimf.layers_1_to_3 import FractalMembraneNetwork, AdaptiveCompressionLayer


# --- BUG 1: lattice decoded every bit as 0 (total silent data loss) ----------

@pytest.mark.parametrize("payload", [
    b"HELLO DEEP TIME",
    b"\x00\xff\x55\xaa",
    b"The unified invariant survives.",
])
def test_lattice_round_trip(payload):
    enc = DiamondLatticeEncoder(lattice_size=16)
    enc.encode_bytes(payload)
    assert enc.decode_bytes(len(payload)) == payload


def test_encoded_bit_reads_back_a_one():
    """110.0 deg is what the encoder writes for a 1; it must decode as 1."""
    assert LatticeDeformation((0, 0, 0), 0.001, bond_angle_deg=110.0).encoded_bit == 1
    assert LatticeDeformation((0, 0, 0), 0.000, bond_angle_deg=109.5).encoded_bit == 0


# --- BUG 2: seal() succeeded on a truncated, unrecoverable archive -----------

def test_oversized_payload_is_rejected_not_truncated():
    m = CryptographicMonolith(lattice_size=16)          # 512-byte capacity
    with pytest.raises(ValueError, match="exceeds lattice capacity"):
        m.load_from_active_system({"payload": "X" * 5000})


def test_seal_verifies_lattice_round_trip():
    m = CryptographicMonolith(lattice_size=32)
    m.load_from_active_system({"epoch": 4471, "axioms": ["causality"]})
    m.seal(background_temp_k=2.725e-10)
    assert m.status()["sealed"] is True
    assert m.status()["integrity_intact"] is True


def test_seal_requires_load_first():
    with pytest.raises(RuntimeError):
        CryptographicMonolith().seal()


# --- BUG 3a: Hausdorff dimension was always exactly 1.0 ---------------------

def test_hausdorff_dimension_varies_with_branching():
    dims = {b: FractalMembraneNetwork(b, 2).hausdorff_dimension() for b in (2, 3, 5)}
    assert len(set(dims.values())) == 3, f"D_H collapsed to a constant: {dims}"
    assert math.isclose(dims[3], math.log(3) / math.log(2), rel_tol=1e-9)


def test_hausdorff_reaches_readme_target_band():
    d = FractalMembraneNetwork(7, 2, scale_factor=3.0).hausdorff_dimension()
    assert 1.7 <= d <= 1.9, f"expected README's 1.7-1.9 band, got {d}"


# --- BUG 3b: energy always 0.0; K ignored content --------------------------

def test_kolmogorov_estimate_separates_random_from_compressible():
    layer = AdaptiveCompressionLayer()
    rng = random.Random(1)
    compressible = layer._store[layer.store(b"x" * 500)]
    noisy = layer._store[layer.store(bytes(rng.getrandbits(8) for _ in range(500)))]
    assert compressible.kolmogorov_complexity < noisy.kolmogorov_complexity
    assert compressible.energy > noisy.energy


def test_verbatim_model_is_reachable():
    """Old length-based K made VERBATIM unreachable below 1 MB."""
    layer = AdaptiveCompressionLayer()
    rng = random.Random(7)
    em = layer._store[layer.store(bytes(rng.getrandbits(8) for _ in range(500)))]
    assert em.model.name == "VERBATIM"


# --- Integration ------------------------------------------------------------

def test_full_stack_cycle_and_darkening():
    hpm = HPMv5()
    report = hpm.run_cycle(write_data=b"observation")
    assert report["coherent"] is True
    assert 0.0 <= report["phi"] <= 1.0

    mono = hpm.initiate_darkening_transition({"epoch": 1}, lattice_size=64)
    assert mono.status()["sealed"] is True
    with pytest.raises(RuntimeError):
        hpm.run_cycle()


def test_rosetta_block_detects_payload_change():
    a = RosettaBlock.encode("rec", {"rec": "civilisation A"})
    b = RosettaBlock.encode("rec", {"rec": "civilisation B"})
    assert a.verify() and b.verify()
    assert a.integrity_hash != b.integrity_hash
