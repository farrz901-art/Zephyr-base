# Manual Base UX Smoke

This manual smoke checks the visible S16 product shell.

## Steps

1. Launch the Base app window.
2. Confirm the main shell shows a language toggle in the header.
3. Switch to `中文`.
4. Confirm the primary labels update to Chinese.
5. Switch back to `English`.
6. Paste the marker `ZEPHYR_BASE_S16_UX_TEXT_MARKER`.
7. Click the primary `Run` button.
8. Confirm the result preview contains the marker.
9. Confirm Advanced diagnostics are collapsed by default.
10. Expand Advanced diagnostics.
11. Confirm receipt, evidence, usage fact, and lineage are visible.

## Truth boundary

This manual smoke does not claim:

- new runtime capability
- PDF, DOCX, image, or OCR support
- signed installer or official release
