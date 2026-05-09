# Manual Tauri window proof

If the visible window cannot be clicked through automation, use this manual proof flow.

Windows example:

1. Open PowerShell and set the Python that should be used by the Rust bridge:
   `$env:ZEPHYR_BASE_PYTHON = (Get-Command python).Source`
2. Run `python scripts/check_python_runtime_dependencies.py --json`
3. Open a VS BuildTools x64 environment.
4. `cd E:\Github_Projects\Zephyr-base`
5. `npm --prefix ui ci`
6. `npm --prefix ui run build`
7. `cargo check --manifest-path src-tauri/Cargo.toml`
8. `cmd /c "\"E:\vs_buildtools\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat\" && cd /d E:\Github_Projects\Zephyr-base && npm --prefix ui run build && cargo run --manifest-path src-tauri/Cargo.toml"`
9. In the window, select `Real Tauri local text`.
10. Enter marker `ZEPHYR_BASE_S10_WINDOW_INTERACTION_MARKER`.
11. Click `Run local text`.
12. Confirm the UI shows:
    - normalized preview containing the marker
    - content evidence
    - receipt
    - usage fact with `billing_semantics=false`
    - output folder plan
13. Click `Export interaction proof`.
14. Run `python scripts/check_tauri_window_interaction_proof.py --json`

Notes:
- `ZEPHYR_BASE_PYTHON` is used by the Rust bridge.
- If `ZEPHYR_BASE_PYTHON` is not set, the bridge falls back to `python`, which may not be the Zephyr environment you expect.
- If no proof JSON exists, S10 can only be conditional.
- A screenshot is helpful but not sufficient by itself.
- `run_result.json` remains the hard evidence artifact.
- This still does not prove installer-complete runtime packaging.
