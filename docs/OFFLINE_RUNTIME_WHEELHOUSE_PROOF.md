# Offline runtime wheelhouse proof

S14 establishes the Base offline wheelhouse and no-index runtime install proof first slice.

## Scope

- The proof target is wheelhouse-based dependency install for the Base runtime.
- The proof target is not an installer, not a signed release, and not embedded Python.
- Wheelhouse files are generated locally under `.tmp/` and are not committed to the repository.
- Virtual environments created for the proof are generated locally under `.tmp/` and are not committed.

## What S14 proves

- `runtime/python-runtime/base-runtime-requirements.txt` can be downloaded into a wheelhouse.
- A managed runtime can be created from that wheelhouse with `pip install --no-index --find-links ...`.
- The managed runtime created from the wheelhouse can run the bundled adapter path.
- Both local-text and local-file Base first-slice runtime flows can pass with `billing_semantics=false`.
- Runtime execution remains `requires_network=false` and `requires_p45_substrate=false`.

## What S14 does not claim

- `installer_built=true`
- `release_created=true`
- `signed_installer=true`
- `embedded_python_runtime=true`
- `wheelhouse_bundled=true` in the repository
- clean-machine external offline proof

## Runtime assumptions

- The host still needs Python 3.12 and pip.
- S14 removes network dependence from dependency installation after the wheelhouse has been built.
- S14 does not claim offline dependency acquisition from scratch; the wheelhouse build step can still use the network.

## Artifact boundaries

- Repository truth remains source, scripts, docs, manifests, and checks.
- Generated wheelhouse artifacts live only under `.tmp/base_runtime_wheelhouse`.
- Generated proof-pack artifacts live only under `.tmp/clean_machine_offline_proof_pack`.
- No Pro, Web-core, license, entitlement, payment, billing, quota, or risk logic is introduced here.
