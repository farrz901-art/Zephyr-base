# Tauri Command Bridge

Zephyr Base uses Rust as the desktop shell and command-bridge layer.

## Ownership
- Rust/Tauri owns desktop-shell orchestration, safe local command dispatch, and result loading.
- The bundled Python adapter remains the local public-core runtime first slice.
- Rust does not rewrite the public core.
- Rust does not call a Zephyr-dev working tree.
- Rust does not call cloud services.
- Rust does not host commercial logic.

## Command surface
The current first slice exposes these command-oriented functions in `src-tauri/src/commands.rs`:
- `run_local_file`
- `run_local_text`
- `read_run_result`
- `open_output_folder_plan`
- `read_lineage_snapshot`

These commands invoke `public-core-bridge/run_public_core_adapter.py` in bundled mode:
- `--bundle-root runtime/public-core-bundle`
- no Zephyr-dev root
- no fixture fallback

## Contract alignment
Rust command outputs align to `base_run_result_v1`.
Errors must stay user-safe and secret-safe.

## Current runtime limits
- This S6 slice still uses the current Python environment.
- `installer_runtime_complete = false`
- `embedded_python_runtime = false`
- `wheelhouse_bundled = false`
- No Tauri window/UI shell is implemented yet.
- No installer is built yet.
