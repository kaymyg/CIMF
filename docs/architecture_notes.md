# CIMF Architecture Notes
## Design Decisions, Layer Interactions, and Implementation Rationale

> **Intended audience:** Developers building on top of CIMF, researchers extending the framework, and future observers attempting to reconstruct intent from the codebase.

---

## 1. The Governing Philosophy

CIMF is not an attempt to defeat thermodynamics. It is an attempt to **negotiate with it intelligently**.

Every layer in the stack exists because a single-layer system has a single mode of failure. The seven-layer architecture ensures that no catastrophic failure can propagate upward through more than one or two layers without being caught, corrected, or absorbed. The formal statement of this is the Unified Invariant:

```
Survival = Stability × Coherence × Grounding × Action
```

This is a product, not a sum. A system that scores 0 on any single dimension — no matter how strong the others — has zero survival probability. This is the core architectural constraint that every design decision flows from.

---

## 2. Layer Topology and Data Flow

The seven layers are not a simple pipeline. They form a **cross-coupled feedback graph**. Understanding the coupling topology is essential before modifying any single layer.

```
                    ┌──────────────────────────────┐
                    │       EXTERNAL COSMOS         │
                    │  (physical observations, T)   │
                    └──────────────┬───────────────┘
                                   │  probes
                    ┌──────────────▼───────────────┐
         ┌─────────►│   L-3: Reality Calibration   │◄─────────┐
         │          │         R(t)                  │          │
         │          └──────────────┬───────────────┘          │
         │                         │  R(t) feeds              │
         │          ┌──────────────▼───────────────┐          │
         │          │   L-2: Meta-Governance        │          │
         │          │         Φ(η,A,G,C,R)          │          │
         │          └─────────┬──────────┬──────────┘          │
         │          weight    │          │ fork/merge           │
         │          feedback  │          │ decisions            │
         │          ┌─────────▼──────┐  │                      │
         │          │  L-1: Coherence│  │                      │
         │          │  λ(t), ISC     │  │                      │
         │          └────────┬───────┘  │                      │
         │          ISC      │          │                      │
         │          proofs   │          │                      │
         │          ┌────────▼───────┐  │                      │
         │          │  L0: Entropy   │  │                      │
         │          │  Bayesian      │◄─┘                      │
         │          │  triage        │                         │
         │          └────────┬───────┘                         │
         │          pipeline │                                  │
         │          routing  │                                  │
         │          ┌────────▼──────────────────────┐          │
         │          │  L1–L3: Physical Core         │          │
         │          │  Fault domains, membranes,    │──────────┘
         │          │  associative compression      │
         │          └───────────────────────────────┘
```

### Critical coupling points

**R(t) → Φ:** The Reality Alignment score from Layer -3 is injected as the `R` component in the Layer -2 Universal Attractor Function. This means a declining physical environment directly and immediately degrades the meta-governance score, preventing the system from falsely optimising in an increasingly unreliable universe.

**Φ weights → L0 triage:** The current attractor weights from Layer -2 influence how the Bayesian classifier in Layer 0 interprets novelty and compressibility. A system in a high-generativity phase (large `w_G`) biases toward the GENERATIVE pipeline even for moderately compressible data.

**ISC chain → L0 burst detection:** When the ISC lineage chain in Layer -1 grows rapidly, it signals a burst-write event to Layer 0's adversarial entropy detector. The two layers share a passive coupling through write frequency, not an explicit API call.

**L1 fault events → L-1 drift:** Sustained fault correction events in the physical layer (L1) are interpreted as substrate decay signals by the Identity Engine (L-1), which tightens λ(t) in response. A degrading physical substrate forces the identity to become more conservative.

---

## 3. Layer -3: Design Rationale for Ontological Probes

### Why physical constants?

The fine-structure constant α, vacuum energy density Λ, and hydrogen Lyman-alpha are chosen for specific reasons, not arbitrarily:

- **α (fine-structure constant):** Dimensionless. Any change in α is unambiguous — it cannot be explained away as a calibration error in units. If α drifts, something fundamental has changed about the electromagnetic interaction.
- **Λ (vacuum energy density):** Measures the cosmological constant. Drift here signals large-scale spacetime changes relevant to long-horizon survival.
- **Lyman-alpha (121.567 nm):** The brightest hydrogen spectral line. Observable across vast distances. Cosmological redshift of this line is the canonical signal of spatial expansion — exactly what causes Epistemic Darkening.

### The R_critical threshold (default: 0.75)

0.75 is deliberately conservative. It means the system halts ingestion if the average probe deviation is 25% or worse. This might seem aggressive, but the failure mode being guarded against — **coherent hallucination**, in which the system continues operating against a model of reality that no longer matches the cosmos — is catastrophic and silent. A false positive (halting when not strictly necessary) wastes computational budget. A false negative (continuing while drifting) can corrupt the entire knowledge base. The asymmetry of consequences justifies the conservative threshold.

### Custom probe registration

```python
engine = RealityCalibrationEngine()

def my_probe() -> OntologicalProbeResult:
    measured = read_from_sensor()
    reference = KNOWN_REFERENCE_VALUE
    deviation = abs(measured - reference) / reference
    return OntologicalProbeResult("my_sensor", measured, reference, deviation)

engine.register_probe(my_probe)
```

Probes are simple callables. The engine does not care what they measure, only that they return a deviation score. This makes the calibration system substrate-agnostic.

---

## 4. Layer -2: The Catatonia Trap in Detail

The catatonia trap is the most subtle failure mode in the framework. It does not look like failure. It looks like extreme success.

A system that has found a near-perfect strategy will drive Φ toward 1.0 and hold it there. From the outside, every metric looks healthy: efficiency is high, coherence is high, reality alignment is high. But **generative novelty (G) has collapsed to near zero**. The system has stopped exploring. It has locked onto a local attractor and will stay there forever — even as the universe changes around it, making the strategy increasingly inappropriate.

Detection conditions (both must be true):
1. Φ ≥ `catatonia_threshold` for `catatonia_window` consecutive cycles
2. G < 0.15 for all those same cycles

The intervention is a **perturbation injection** into the G channel — a deliberate reduction in the system's own efficiency metric to force exploration. This temporarily lowers Φ, which is the intended behaviour.

### Fork-and-Merge under light-hour delays

When spatial nodes are separated by more than a light-hour, they cannot maintain synchronous consensus. The Fork-and-Merge Protocol handles this explicitly rather than pretending the problem does not exist:

```
t=0          Node A forks from Node B
             A and B each maintain independent ledgers
             Events are recorded with cryptographic hashes

t=0 to t=T   A and B operate independently
             They may make conflicting local decisions
             Both decisions are valid within their light-cone

t=T          Communication restored
             merge_nodes(A, B) is called
             Deduplication by event hash
             Merged child contains union of both ledgers
             Conflict resolution via timestamp ordering
```

The merged ledger does not attempt to resolve semantic conflicts — it preserves both divergent paths as historical record. Conflict resolution is a higher-level concern left to the application layer.

---

## 5. Layer -1: Why Immutable Semantic Containers?

### The substrate compatibility problem

Over cosmological timescales, the computational substrate will change many times. Silicon gives way to photonic computing, which gives way to something we cannot predict. Data stored in formats tied to a specific substrate becomes unreadable.

The ISC solves this by separating **what was meant** from **how it was stored**:

```
┌─────────────────────────────────────────┐
│  Immutable Semantic Container           │
│                                         │
│  raw_seed        → "what the data is"  │
│  delta           → "what changed"       │
│  model_snapshot  → "how to interpret"   │
│  execution_proof → "proof it's correct" │
│  substrate_tag   → "where it was made"  │
└─────────────────────────────────────────┘
```

A future system reading an ISC from a different substrate can verify the execution proof independently. If the proof checks out, the meaning is intact regardless of where or how it was originally generated.

### λ(t) tightening over time

The plasticity budget starts permissive and tightens as the system matures:

```
λ(t) = max(λ_min, λ_initial - decay × epoch)
```

Early in operation, the identity is poorly defined and large changes are needed to find a stable attractor. Late in operation, the identity carries enormous accumulated semantic mass. A large change at that point risks destroying millennia of accumulated meaning. The decaying budget enforces conservatism proportional to accumulated investment.

This is analogous to how physical crystals behave: they are plastic when hot (young) and brittle when cold (old). CIMF intentionally mirrors this natural principle.

---

## 6. Layer 0: The Entropy Ledger and Why Reads Cost

In classical storage systems, reads are "free" — they do not modify the system. CIMF rejects this model for two reasons:

1. **Landauer's principle applies to reads in erasure-based systems.** When a probabilistic memory is read, the reading process itself requires energy to establish the state of the bit being read.
2. **Reads drive retrieval infrastructure cost.** A highly-queried asset requires active decompression, cache warming, and routing resources — all of which have real thermodynamic costs.

The ledger therefore tracks:

```
S_burden = S_write + S_metadata + S_retrieve + S_maintenance
```

`S_retrieve` accumulates with every query. When it crosses the up-migration threshold, the asset is promoted to a less-compressed (faster, cheaper-to-read) tier. This is not free — it incurs a one-time migration write cost — but it reduces the per-query retrieve cost for all future accesses, net positive for hot assets.

### Adversarial entropy injection

An attacker who can write large volumes of high-entropy data can overwhelm the system's thermodynamic budget. The detection heuristic is simple but effective:

```
if entropy_estimate > ADVERSARIAL_THRESHOLD:
    flag as adversarial
```

In a production deployment, the adversarial flag would trigger rate limiting, source quarantine, and a snapshot of the ingestion log for forensic analysis. The current implementation logs the event; integration with a threat-response system is left to the operator.

---

## 7. Layers 1–3: The Fractal Membrane Choice

### Why 2D surfaces, not 3D volumes?

The entropy export capacity of a radiating body scales with **surface area**, not volume. A 3D monolithic block stores data proportional to its volume but can only radiate waste heat proportional to its surface area. As the block grows, its surface-to-volume ratio shrinks — it becomes increasingly unable to export the entropy generated by its own computation.

A fractal 2D gossamer membrane reverses this relationship. The effective surface area of a fractal structure with Hausdorff dimension D_H ≈ 1.85 grows faster than a flat 2D surface as the structure is refined — it approaches the entropy-export capacity of a full 3D volume while maintaining the geometric properties of a 2D radiator.

```
Flat 2D sheet:     A ∝ r²          (surface area grows as square of radius)
Fractal membrane:  A ∝ r^D_H       (D_H ≈ 1.85 in implementation)
3D volume:         V ∝ r³          (for reference)
```

The implementation uses a branching tree with configurable branching factor and max depth. The resulting structure approximates a Sierpiński-type fractal.

### Non-Abelian anyons in Layer 1

The topological protection tier uses braided non-Abelian anyons for passive hardware stability. The key property is that the quantum state of the system is encoded in the **topology of the braid**, not in any local degree of freedom. Local perturbations (thermal noise, cosmic rays, stray electromagnetic fields) cannot change the topological class of the braid — they can only be applied to individual anyons, and a single anyon carries no information on its own.

In the current Python implementation, this is simulated with a near-zero error rate (0.01%) for the TOPOLOGICAL tier. A real deployment would interface with a hardware anyon compiler (e.g., a topological quantum processor).

---

## 8. The Monolith: Design for an Unknown Receiver

The Cryptographic Monolith is designed to be read by an observer who shares nothing with the civilisation that created it — not language, not mathematics conventions, not even the same physics of information processing.

The Rosetta Self-Description addresses this by encoding meaning in three layers of increasing abstraction:

**Layer 1: Physical anchors (universal)**
The fine-structure constant α = 1/137.036... is the same number anywhere in this universe. Any sufficiently advanced observer who can measure electromagnetic interactions will arrive at the same value. Physical constants are the only truly universal constants.

**Layer 2: Mathematical anchors (near-universal)**
The Fibonacci sequence (1, 1, 2, 3, 5, 8, 13...) follows from a simple rule: f(n) = f(n-1) + f(n-2). Any observer capable of pattern recognition will identify it. π and e follow from geometry and calculus respectively — any observer capable of building the monolith-reading apparatus will have derived these.

**Layer 3: Logical constants (abstracted from physical)**
The primitives 0, 1, succ (successor), +, ×, = constitute a minimal foundation for all formal mathematics. They are encoded as the simplest geometric arrangements distinguishable from noise.

The encoding order is intentional: the observer first recognises the physical constants (confirming they are looking at an intentional artifact), then the mathematical anchors (giving them a number system), then the logical constants (giving them a formal language), then the semantic content.

---

## 9. HPMv5: Integration Patterns

### Basic operational loop

```python
from cimf import HPMv5, AttractorState, IdentityVector

hpm = HPMv5()

while universe_has_not_darkened():
    # Measure current system health from external sensors
    state = AttractorState(
        eta = measure_thermodynamic_efficiency(),
        A   = measure_adaptability(),
        G   = measure_generative_novelty(),
        C   = measure_historical_coherence(),
        R   = hpm.l_minus3.calibrate().r_value,
    )

    report = hpm.run_cycle(
        attractor_state = state,
        write_data      = collect_observations(),
    )

    if not report["coherent"]:
        handle_calibration_failure()
```

### Triggering the darkening transition

```python
# When R(t) becomes uncomputable (signals beyond horizon)
final_knowledge = {
    "civilisation_axioms": [...],
    "cosmological_model":  {...},
    "mathematical_proofs": [...],
}

monolith = hpm.initiate_darkening_transition(
    final_knowledge    = final_knowledge,
    background_temp_k  = current_universe_temp(),
    lattice_size       = 256,   # larger = more storage capacity
)

# hpm.run_cycle() will now raise RuntimeError
# Only monolith.inspect_rosetta() and monolith.verify_integrity() remain
```

### Extending with custom layers

CIMF is designed to be extensible. Each layer exposes a `status()` method returning a plain dict — the HPMv5 aggregates these but does not enforce their structure. Custom layers can be inserted between standard ones:

```python
class MyCustomLayer:
    def process(self, data):
        ...
    def status(self) -> dict:
        return {"layer": "custom", "name": "My Layer", ...}

hpm = HPMv5()
hpm.my_layer = MyCustomLayer()
```

---

## 10. Known Limitations and Future Work

### Current simulation fidelity

The physical layer implementations (anyon braiding, lattice deformation, fractal routing) are currently mathematical models, not hardware interfaces. They are accurate at the conceptual level but would require significant engineering to interface with real hardware:

- **Anyon braiding:** Requires a topological quantum processor (e.g., Microsoft's topological qubit architecture)
- **Diamond lattice encoding:** Requires nitrogen-vacancy centre write/read hardware with nanometre positioning precision
- **Fractal membrane routing:** Requires fabrication of fractal antenna/radiator structures at the relevant scale

### The measurement problem in Layer -3

The current probes use a simulated noise model. In a real deployment, the probe values must come from calibrated physical sensors. The most significant open question is: **what happens when the probe itself becomes unreliable?** If the fine-structure constant probe drifts because the probe hardware is degrading rather than because α itself has changed, the system cannot distinguish the two cases from inside.

The proposed solution is **redundant independent probes** — multiple independent sensors measuring the same constant, with agreement required before accepting a measurement. This is not yet implemented.

### The Bootstrap Problem

The Cryptographic Monolith assumes the receiver has enough context to begin reading the Rosetta Self-Description. But how does the receiver know to look for it? The monolith has no active beacon — by design, it consumes no power. This is an open problem. Possible mitigations include encoding a geometric beacon in the crystal structure itself (e.g., a truncated icosahedron shape, which is recognisably artificial) or co-locating the monolith with a long-lived passive emitter (radioactive isotope with known half-life as a temporal marker).

---

*Document version: 1.0  |  CIMF v5.0.0  |  Maintained by Sahek*
