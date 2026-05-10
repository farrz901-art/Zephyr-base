# Windows Packaging

This directory holds the auditable schema and documentation for the S15 Windows installer packaging first slice.

Current S15 output:
- `package_kind=portable_zip`
- `signed_installer=false`
- `release_created=false`
- `embedded_python_runtime=false`

The packaged payload is designed to be unpacked into a Windows install root, bootstrap a managed runtime from the bundled wheelhouse, and run the local text or file smoke path without network access at runtime.
