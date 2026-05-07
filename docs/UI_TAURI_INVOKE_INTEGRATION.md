# UI Tauri Invoke Integration

P6-M3-S8 verifies command-name and payload alignment between the Zephyr Base Web UI shell and the Rust/Tauri command bridge.

## Scope

- The Rust/Tauri layer remains the desktop shell and command bridge.
- The bundled Python adapter remains the local public-core runtime first slice.
- The UI consumes `base_run_result_v1` as the single result source.
- The UI does not own processing logic.
- The UI does not call Python directly.
- The UI does not call Zephyr-dev.
- The UI does not call cloud, network services, Web-core, Pro, or commercial logic.
- The Base runtime still uses the current Python environment.
- `installer_runtime_complete=false` remains true in this slice.

## S8 verification approach

S8 does not require opening a Tauri window.
Instead, it verifies the same command surface through a windowless Rust CLI / command-bridge path that uses the bundled adapter and produces real `run_result.json` artifacts.

This makes S8 an invoke-equivalent smoke rather than a full window e2e proof.

## Command alignment

The UI client and Rust bridge align on these command names:

- `run_local_file`
- `run_local_text`
- `read_run_result`
- `open_output_folder_plan`
- `read_lineage_snapshot`

The UI payloads stay limited to local Base first-slice needs:

- `run_local_file`: `input_path`, `output_dir`
- `run_local_text`: `inline_text`, `output_dir`
- `read_run_result`: `output_dir`
- `open_output_folder_plan`: `output_dir`

## Result lifecycle

S8 verifies the local result lifecycle in four stages:

1. prepare request payload
2. invoke the Rust/Tauri bridge or read an existing artifact
3. consume `run_result.json`
4. classify and expose success / error / normalized text / evidence / receipt / usage fact / output folder plan

## Current limitation

- Tauri window e2e is still not fully proven in S8.
- S8 is not an installer.
- S8 is not a release build.
- S8 does not provide embedded Python or wheelhouse packaging yet.
