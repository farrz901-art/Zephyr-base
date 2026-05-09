# Clean Machine Runtime Proof Plan

S12 does not complete clean-machine runtime proof.

`clean_machine_runtime_proven = false` remains explicit.

Later installer/runtime phases should validate the following on a clean Windows VM:
1. obtain the install layout or installer precursor
2. bootstrap the managed runtime from the packaged runtime manifest
3. launch the visible Base app path
4. run local text and local file flows
5. confirm bundled runtime usage, `billing_semantics = false`, and local-only execution
6. verify uninstall or cleanup expectations

This later proof must not claim:
- embedded Python unless it is actually packaged
- offline install unless wheelhouse/offline evidence is complete
- Web-core, Pro, private core, or commercial logic
