# Packaged Runtime Baseline

P6-M3-S11 establishes a managed local Python runtime first slice for Zephyr Base.

## Scope
- create a runtime dependency manifest for the Base first slice
- bootstrap a managed local virtual environment under `.tmp/base_runtime_venv`
- support a repo-local fallback managed runtime path recorded in `.tmp/base_runtime_python_path.txt` when the default path is stale or locked
- support an optional wheelhouse preparation path for local validation
- expose runtime selector and preflight facts so the Rust bridge can use a managed runtime
- prove that the bundled adapter can run through a managed local runtime

## Explicit non-goals
- this is not an installer-complete runtime
- this does not prove a clean-machine installer flow
- this does not vendor secrets or runtime-home state
- this does not add Web-core, Pro, license, entitlement, payment, billing, quota, or risk logic
- this does not expand the supported format surface beyond `.txt`, `.text`, `.log`, `.md`, `.markdown`

## Runtime truth
- `embedded_python_runtime = false`
- `installer_runtime_complete = false`
- `wheelhouse_bundled = false`
- `managed_venv_supported = true`
- runtime execution remains local-only and does not require the Zephyr-dev working tree

## What S11 adds
- `runtime/python-runtime/base-runtime-requirements.in`
- `runtime/python-runtime/base-runtime-requirements.txt`
- `runtime/python-runtime/runtime_manifest.json`
- `scripts/bootstrap_base_runtime.py`
- `scripts/check_python_runtime_dependencies.py` updates for managed-runtime selection
- `scripts/check_managed_runtime_flow.py`
- optional wheelhouse preparation and install-validation scripts

## Offline and packaging limits
S11 may prepare a local wheelhouse for validation, but it does not claim an offline installer-complete runtime unless a separate wheelhouse install proof passes. Wheel files are not committed to the repository in this slice.

## Bootstrap fallback note
If the default managed runtime path is stale or locked, bootstrap may create a repo-local fallback managed runtime and record that interpreter path in `.tmp/base_runtime_python_path.txt`. That still proves a managed interpreter path, but it does not claim clean-machine isolation or installer completeness.
