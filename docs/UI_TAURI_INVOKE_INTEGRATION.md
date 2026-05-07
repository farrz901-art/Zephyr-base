# UI Tauri Invoke Integration

Zephyr Base S8 and later treats `base_run_result_v1` as the single result contract that
the UI consumes after local processing finishes.

## What S8/S9 verify

- UI command names and payload fields align with the Rust/Tauri command bridge.
- Windowless CLI smoke is used as an invoke-equivalent validation path.
- S9 adds a real Tauri app registration path and a built UI dist baseline.
- Full window click automation is still optional and is not claimed unless explicitly run.

## Ownership

- UI does not own processing logic.
- UI does not call Python directly.
- UI does not call Zephyr-dev.
- UI does not call cloud, Web-core, or any network service.
- UI does not contain license, entitlement, payment, billing, quota, or risk logic.

## Runtime truth

- UI invokes Rust/Tauri commands.
- Rust/Tauri invokes the bundled adapter.
- The bundled adapter still uses the current Python environment in this first slice.
- `installer_runtime_complete=false` remains true until a later M3 packaging slice lands.

## Current limitation

The Tauri window path is now launch-ready and command-registered, but full click-driven
desktop e2e is still a later manual or automated proof step.
