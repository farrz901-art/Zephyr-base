# Clean-machine runtime proof

P6-M3-S13 establishes the Zephyr Base clean-machine runtime proof path at proof level L1.

## Scope

- L1 is a clean Windows runtime proof path, not an installer or release proof.
- L1 allows a clean Windows machine that already has Python 3.12, `pip`, and network access.
- L1 does not require Git, Node/npm, Rust/Cargo, Zephyr-dev, or a Zephyr-base git checkout.
- L1 does not require P4.5 substrate, Web-core, Pro, private core, or commercial logic.

## Required proof artifacts

A valid clean-machine proof requires all of the following from the unpacked clean proof pack:

- `proof/clean_machine_runtime_proof.json`
- `proof/clean_machine_runtime_proof_validation.json`
- `proof/clean_machine_text/run_result.json`
- `proof/clean_machine_file/run_result.json`
- the unpacked layout root used to create those artifacts

The proof runner must bootstrap a layout-local managed runtime and run both:

- local text smoke
- local file smoke for `.txt` or `.md`

## Claims S13 does not make

- `embedded_python_runtime=true`
- `wheelhouse_bundled=true`
- `installer_built=true`
- `release_created=true`
- offline install complete

## Runtime truth

- bootstrap may use network to install dependencies into a layout-local managed runtime
- runtime execution itself must still report `requires_network=false`
- runtime execution must still report `requires_p45_substrate=false`
- runtime execution must not require a Zephyr-dev working tree
- runtime execution must not fall back to fixtures
