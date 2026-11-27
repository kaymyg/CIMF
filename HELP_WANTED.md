# Help wanted

🌌 Cosmological Information Management Framework is open to contributions. Below is the hardening work that would make it stronger, roughly in order of impact. Pick anything, comment on (or open) an issue so others know you are on it, and see [CONTRIBUTING.md](CONTRIBUTING.md) to get started.

Found a vulnerability instead? Please report it privately, see [SECURITY.md](SECURITY.md).


### Add a citation check for taxonomy entries

**Good first issue.** Every entry should point to a source. A small test that fails when an entry has no reference would keep the taxonomy honest.

### Property-based tests for `cimf/`

**Medium.** Use Hypothesis to generate inputs for the core functions and assert their invariants instead of fixed examples.

### Type hints and mypy in CI

**Medium.** Add annotations to the public functions and a `mypy --strict` step so regressions show up in review.
