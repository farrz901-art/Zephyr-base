# Zephyr Base Python Runtime

This directory describes the managed Python runtime baseline for Zephyr Base.

## Current scope
- supports the Base first-slice local formats: `.txt`, `.text`, `.log`, `.md`, `.markdown`
- supports a managed virtual environment bootstrap under `.tmp/base_runtime_venv`
- supports a repo-local fallback managed runtime path recorded in `.tmp/base_runtime_python_path.txt` when the default path is stale or locked
- supports optional wheelhouse preparation for local validation

## Current limitations
- not an embedded Python runtime
- not an installer-complete runtime
- not a clean-machine installer proof
- does not vendor secrets, runtime-home state, Web-core, Pro, or commercial logic

## Usage
1. Run `python scripts/bootstrap_base_runtime.py --json`.
2. Optionally inspect `.tmp/base_runtime_python_path.txt` to see the selected managed interpreter path.
3. Optionally set `ZEPHYR_BASE_PYTHON` to the managed runtime path.
4. Run `python scripts/check_managed_runtime_flow.py --json`.

The managed runtime remains a local development and validation slice until a later installer-packaging step closes the runtime distribution gap.

## Bootstrap fallback note
If the default managed runtime path is stale or locked, bootstrap may create a repo-local fallback managed runtime and record that interpreter path in `.tmp/base_runtime_python_path.txt`. That still proves a managed interpreter path, but it does not claim clean-machine isolation or installer completeness.
