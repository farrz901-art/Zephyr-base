# Base Install Layout Policy

S12 defines an install-layout first slice for Zephyr Base. This is an installer precursor, not a signed installer or release artifact.

Canonical layout:

```text
.install-layout/ZephyrBase/
  app/
    zephyr-base-app-placeholder.txt
    ui/dist
    tauri.conf.snapshot.json
  public-core-bridge/
  runtime/
    public-core-bundle/
    python-runtime/
  manifests/
    public_export_lineage.json
    install_layout_manifest.json
  docs/
    README.md
    NOTICE.md
    PRODUCT_BOUNDARY.md
    PACKAGED_RUNTIME_BASELINE.md
    BASE_LOCAL_APP_FLOW.md
  checks/
    bootstrap_base_runtime.py
    check_python_runtime_dependencies.py
    check_managed_runtime_flow.py
```

S12 policy:
- the layout is a local install-layout slice, not a final MSI/NSIS installer
- the layout does not claim clean-machine runtime proof
- the layout does not embed Python
- the layout does not vendor a managed venv
- the layout does not vendor secrets
- the layout does not vendor Web-core, Pro, private core, or commercial logic
- the layout does include runtime manifests, bundled public-core runtime, public-core bridge, UI dist, runtime bootstrap/check helpers, NOTICE, LICENSE, and product-boundary materials

Truth markers that must remain explicit:
- `installer_built = false`
- `release_created = false`
- `embedded_python_runtime = false`
- `wheelhouse_bundled = false`
- `clean_machine_runtime_proven = false`
- `managed_venv_supported = true`
