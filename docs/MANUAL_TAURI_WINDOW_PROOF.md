# Manual Tauri window proof

If the visible window cannot be clicked through automation, use this manual proof flow.

Windows example:

1. Open a VS BuildTools x64 environment.
2. `cd E:\Github_Projects\Zephyr-base`
3. `npm --prefix ui ci`
4. `npm --prefix ui run build`
5. `cargo check --manifest-path src-tauri/Cargo.toml`
6. `cargo run --manifest-path src-tauri/Cargo.toml`
7. In the window, select `Real Tauri local text`.
8. Enter marker `ZEPHYR_BASE_S10_WINDOW_INTERACTION_MARKER`.
9. Click `Run local text`.
10. Confirm the UI shows:
    - normalized preview containing the marker
    - content evidence
    - receipt
    - usage fact with `billing_semantics=false`
    - output folder plan
11. Click `Export interaction proof`.
12. Run `python scripts/check_tauri_window_interaction_proof.py --json`

Notes:
- If no proof JSON exists, S10 can only be conditional.
- A screenshot is helpful but not sufficient by itself.
- `run_result.json` remains the hard evidence artifact.
