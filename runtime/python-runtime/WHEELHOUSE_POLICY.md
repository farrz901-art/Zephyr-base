# Wheelhouse policy

This directory defines the Base runtime dependency set and the offline wheelhouse proof policy.

## Rules

- Wheelhouse artifacts are generated from `base-runtime-requirements.txt`.
- Wheelhouse artifacts are local proof artifacts, not committed repository assets.
- `wheelhouse_bundled=false` remains true for the repository baseline.
- `wheelhouse_bundled=true` may appear only inside generated proof packs under `.tmp/`.
- Offline proof means `pip install --no-index --find-links ...` succeeds against the generated wheelhouse.
- Offline proof does not imply installer completeness or embedded Python.

## Current state

- managed runtime first slice: supported
- offline wheelhouse proof first slice: S14
- clean-machine external offline proof: deferred
- embedded Python: false
- installer runtime complete: false
