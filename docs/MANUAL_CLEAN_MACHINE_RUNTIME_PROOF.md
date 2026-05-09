# Manual clean-machine runtime proof

This is the manual L1 clean-machine runtime proof flow for P6-M3-S13.

## Preconditions

- Clean Windows VM or clean Windows machine
- Python 3.12 installed and added to `PATH`
- Network access available for runtime bootstrap
- Git is not required
- Node/npm is not required
- Rust/Cargo is not required
- Zephyr-dev is not required
- Zephyr-base git clone is not required

## Steps

1. Copy `ZephyrBase-clean-machine-proof.zip` to the clean machine.
2. Unzip it to a directory such as `C:\ZephyrBaseProof\ZephyrBase`.
3. Open PowerShell.
4. Run:

```powershell
cd C:\ZephyrBaseProof\ZephyrBase
python checks\run_clean_machine_runtime_proof.py --json
python checks\validate_clean_machine_runtime_proof.py --json
```

5. Confirm that both commands pass.
6. Return these files:

- `proof/clean_machine_runtime_proof.json`
- `proof/clean_machine_runtime_proof_validation.json`
- `proof/clean_machine_text/run_result.json`
- `proof/clean_machine_file/run_result.json`

## Notes

- This is not installer proof.
- This is not offline proof.
- This is not embedded Python proof.
- Runtime bootstrap may use network, but runtime execution must still report `requires_network=false`.
