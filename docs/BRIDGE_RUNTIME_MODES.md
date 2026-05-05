# Bridge Runtime Modes

## Fixture mode

- purpose: S3 regression only
- fixture_runner_used: true
- production_runtime: false
- zephyr_dev_public_core_invoked: false
- bundled_runtime_used: false

## Dev real adapter mode

- purpose: S4 real local adapter first slice
- fixture_runner_used: false
- production_runtime: true
- zephyr_dev_public_core_invoked: true
- bundled_runtime_used: false
- bridge mode for local_text may be `temp_file_to_public_core`
- requires a local `ZEPHYR_DEV_ROOT`

## Bundled public-core mode

- purpose: S5 bundled public-core runtime first slice
- fixture_runner_used: false
- production_runtime: true
- bundled_runtime_used: true
- zephyr_dev_working_tree_required: false
- uses current Python environment
- installer_runtime_complete: false
- does not require `ZEPHYR_DEV_ROOT` at execution

## Future installer-bundled mode

- purpose: later M3 clean-machine runtime packaging
- fixture_runner_used: false
- production_runtime: true
- bundled_runtime_used: true
- embedded Python or equivalent packaged runtime
- clean-machine install target

## Rules

- S4 cannot be sealed by fixture mode.
- S5 cannot be sealed by fixture mode.
- S5 cannot be sealed by `--zephyr-dev-root` execution.
- S5 may rely on the current Python environment, but it must truthfully mark `installer_runtime_complete = false`.
