# Base MVP Product Truth

Zephyr Base is a free local-only desktop product for plain-text and Markdown normalization.

## Supported user-visible capabilities

1. Paste local text and process it.
2. Process a local file path for `.txt`, `.text`, `.log`, `.md`, and `.markdown`.
3. Generate `normalized_text.txt`.
4. Generate `content_evidence.json`.
5. Generate `receipt.json`.
6. Generate `usage_fact.json`.
7. Generate `run_result.json`.
8. Show a normalized preview summary in the UI.
9. Show result summary, evidence summary, and output location in the UI.
10. Support English and Chinese UI labels.
11. Run locally without Zephyr-dev, without P4.5 substrate, and without network access at runtime.

## Explicitly unsupported in Base M3

1. PDF.
2. DOCX.
3. Image or OCR processing.
4. HTML. Base does not expose HTML in M3.
5. Cloud processing.
6. Login.
7. Accounts.
8. License-gated features.
9. Entitlement flows.
10. Payment, billing, or quota controls.
11. Pro-only features.
12. Auto update.
13. Signed installer.

## Product truth for M3

- Base remains free and local-only.
- Base package kind remains `portable_zip`.
- `signed_installer=false`.
- `official_release=false`.
- `release_created=false`.
- `auto_update=false`.
- `embedded_python_runtime=false`.
- `runtime_capability_changed=false`.
