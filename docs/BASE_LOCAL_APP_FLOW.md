# Base Local App Flow

Zephyr Base local app flow in the current M3 slice is:

`UI -> Tauri invoke -> Rust bridge -> bundled adapter -> run_result artifacts -> UI display`

## Supported local inputs

- `.txt`
- `.text`
- `.log`
- `.md`
- `.markdown`

## Current runtime limitations

- Uses the current Python environment.
- Installer runtime is not complete yet.
- Embedded Python runtime is not bundled yet.
- Full window click e2e may still be manual or limited.

## Explicit non-goals in this slice

- No cloud calls.
- No Pro or Web-core.
- No license, entitlement, payment, billing, quota, or risk decision logic.
- No installer or release artifact.
