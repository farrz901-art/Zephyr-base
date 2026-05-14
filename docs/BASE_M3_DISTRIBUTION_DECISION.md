# Base M3 Distribution Decision

## Decision

- M3 delivery artifact: unsigned portable zip preview package.
- Recommended filename: `ZephyrBase-windows-unsigned.zip`.
- Recommended hosting for M3: GitHub Release or GitHub repository release artifact.
- Website distribution can link to a GitHub Release later instead of hosting the binary directly.
- No paid CDN is required for Base M3.
- No controlled download service is required for Base M3.

## Deferred beyond M3

- Official signed installer is deferred to P6-M8 signing and distribution hard gates.
- Auto update is deferred to P6-M8 update manifest hard gates.
- This M3 artifact is a Windows portable zip preview package, not a formal signed installer.

## Truth boundaries

- `package_kind=portable_zip`
- `signed_installer=false`
- `official_release=false`
- `release_created=false`
- `auto_update=false`
- `embedded_python_runtime=false`
