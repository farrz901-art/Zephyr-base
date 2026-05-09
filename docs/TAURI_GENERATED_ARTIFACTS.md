# Tauri Generated Artifacts

`src-tauri/gen/` is a generated output area, not a source-of-truth configuration surface.

Current generated files include:
- `schemas/capabilities.json`: generated aggregate capability view
- `schemas/desktop-schema.json`: generated desktop capability schema
- `schemas/windows-schema.json`: generated Windows capability schema
- `schemas/acl-manifests.json`: generated Tauri/plugin ACL manifest view

Source-of-truth remains:
- `src-tauri/capabilities/default.json` for the checked-in capability config
- `src-tauri/tauri.conf.json` for the checked-in Tauri app config

S12 hygiene rules:
- `src-tauri/gen/` must not be treated as the primary source config
- `src-tauri/gen/` must not be committed as product source
- generated schema snapshots may exist locally for inspection, but the repo should rely on real capability/config inputs
