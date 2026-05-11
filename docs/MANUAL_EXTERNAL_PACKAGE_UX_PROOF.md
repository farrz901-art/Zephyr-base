# Manual external package UX proof

This manual proof validates the Base portable package from an external user perspective.

This is not a signed installer proof, not an official release proof, and not an embedded
Python proof.

## Steps

1. Build or locate:
   - `.tmp/windows_installer_package/ZephyrBase-windows-unsigned.zip`
2. Copy the zip to an external directory or clean machine, for example:
   - `D:\ZephyrBaseUxProof\`
3. Extract it to:
   - `D:\ZephyrBaseUxProof\ZephyrBase`
4. Launch the Base app from the extracted directory.
5. Confirm the shell shows:
   - `Zephyr Base`
   - `Local-only` / `本地运行`
   - a language toggle
6. Switch to 中文 and confirm the main labels change.
7. Switch back to English.
8. Paste this marker and run the primary action:
   - `ZEPHYR_BASE_S17_EXTERNAL_UX_TEXT_MARKER`
9. Confirm the result preview contains the marker.
10. Run a local `.txt` file containing:
    - `ZEPHYR_BASE_S17_EXTERNAL_UX_FILE_MARKER`
11. Confirm the output location is visible.
12. Confirm Advanced is collapsed by default.
13. Expand Advanced and confirm:
    - receipt
    - evidence
    - usage fact
    - lineage
    - proof export
14. Confirm the UI does not claim:
    - PDF
    - DOCX
    - image or OCR
    - cloud processing
    - Pro
    - login
    - license or entitlement
    - payment or billing
15. Fill in an external UX proof JSON using the S17 template.
16. Return the proof JSON and any optional screenshots.
