# Bridge Runtime Modes

## Fixture mode

- purpose: S3 regression only
- fixture_runner_used: true
- production_runtime: false
- zephyr_dev_public_core_invoked: false

## Dev real adapter mode

- purpose: S4 real local adapter first slice
- fixture_runner_used: false
- production_runtime: true
- zephyr_dev_public_core_invoked: true
- bridge mode for local_text may be `temp_file_to_public_core`
- requires a local `ZEPHYR_DEV_ROOT`

## Future bundled mode

- purpose: later M3 Base runtime packaging
- fixture_runner_used: false
- zephyr_dev_public_core_invoked: false at end-user runtime
- production_runtime: true
- public core subset is bundled into Base packaging

## Rule

S4 cannot be sealed by fixture mode. If the real adapter flow fails, S4 remains open or blocked.
