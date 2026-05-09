# Tauri window interaction proof

S10 proves the visible Base window path through the full local chain:

UI window -> Tauri invoke -> Rust command bridge -> bundled adapter -> run_result artifacts -> UI display

Window-click proof prefers automation when the environment supports it. When automation is unstable, S10 allows manual proof instead of fabricated success.

Manual proof must include a proof pack, not a verbal note:
- `.tmp/s10_tauri_window_interaction/run_result.json`
- `.tmp/s10_tauri_window_interaction/ui_interaction_proof.json`
- optional screenshot path or screenshot note
- command or launch metadata
- a marker such as `ZEPHYR_BASE_S10_WINDOW_INTERACTION_MARKER`

Before launching the visible window on Windows, confirm the runtime Python:
- `$env:ZEPHYR_BASE_PYTHON = (Get-Command python).Source`
- `python scripts/check_python_runtime_dependencies.py --json`

`ZEPHYR_BASE_PYTHON` is consumed by the Rust bridge. If it is not set, the bridge falls back to `python`, which may not resolve to the Zephyr environment with Base runtime dependencies.

S10 does not claim:
- installer runtime completeness
- release packaging
- embedded Python runtime
- wheelhouse bundling
- clean-machine runtime

Current runtime truth remains:
- local-only
- bundled adapter
- uses_current_python_environment=true
- installer_runtime_complete=false
- supported formats limited to `.txt`, `.text`, `.log`, `.md`, `.markdown`

Forbidden surfaces remain unchanged:
- no cloud
- no Web-core
- no Pro
- no license
- no entitlement
- no payment
- no billing decision
- no quota authority
- no risk decision
