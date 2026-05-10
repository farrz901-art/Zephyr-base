# Windows Installer Packaging Policy

S15 establishes an unsigned Windows installer or installable package first slice for Zephyr Base.

This slice allows either:
- a portable zip package, or
- an unsigned installer skeleton

S15 does not claim:
- signed installer
- official release
- auto update
- official download channel

The S15 package must include:
- Tauri app executable or launchable skeleton
- UI dist
- bundled public-core runtime assets
- runtime manifests
- runtime Python requirements
- wheelhouse artifact inside the package
- install smoke runner
- boundary and notice documents

The S15 package must not include:
- `.git`
- Zephyr-dev
- Zephyr-base repo metadata beyond the packaged payload
- `node_modules`
- `target` build cache beyond selected final app output
- `src-tauri/gen` generated cache
- `.tmp` virtual environments
- imported proof artifacts
- secrets
- Pro, Web-core, private-core, or commercial logic

Current runtime truth for S15:
- the install package may still require a system Python 3.12 with `pip`
- `embedded_python_runtime=false`
- `installer_runtime_complete=partial`
- `signed_installer=false`
- `release_created=false`

The package is intended as an installer precursor with auditable contents and install-root smoke coverage, not as a production-complete Windows installer.
