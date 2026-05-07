# UI Artifact Consumption

Zephyr Base UI consumes `base_run_result_v1` artifacts produced by the bundled adapter.

## Ownership
- UI does not own processing logic.
- UI does not call a Zephyr-dev working tree.
- UI does not call cloud services.
- UI does not contain license, entitlement, payment, quota, or risk decisions.
- UI displays technical usage facts only.

## Runtime model
- S7 uses mock/sample artifact mode plus a Tauri invoke-ready client wrapper.
- Tauri invoke wiring is prepared but not yet end-to-end verified in this slice.
- The bundled adapter remains the local runtime owner.
- `billing_semantics = false` must stay visible or preserved.

## Current limits
- Full Tauri window integration lands later in M3.
- Installer packaging lands later in M3.
- The current runtime still depends on the current Python environment.
- `installer_runtime_complete = false` remains explicit.
