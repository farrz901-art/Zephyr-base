# Base M3 Final Seal

P6-M3 final status is sealed and pass.

## Delivery artifact

- Base M3 delivery artifact: unsigned portable zip preview package
- Recommended filename: `ZephyrBase-windows-unsigned.zip`

## Recommended M3 distribution

- Recommended hosting: GitHub Release or repository release artifact
- Future Site or website may link to a GitHub Release instead of hosting binaries directly
- No paid CDN is required for Base M3
- No controlled download service is required for Base M3

## User-visible Base capability

- Paste local text and process it
- Process a local `.txt`, `.text`, `.log`, `.md`, or `.markdown` file path
- Run locally
- Use a bilingual UI in English and Chinese
- Produce `normalized_text.txt`, `content_evidence.json`, `receipt.json`, `usage_fact.json`, and `run_result.json`

## Explicit non-goals for M3

- Signed installer
- Official release
- Auto update
- Controlled download
- Pro, Web-core, cloud, or API capability
- PDF, DOCX, image, OCR, or HTML support
- License, entitlement, payment, billing, or quota logic

## Go / no-go

- `go=true`
- `allowed_next_phase=P6-M4`

## Deferred items

- Signed installer: P6-M8
- Update manifest and auto update: P6-M8
- Controlled download hard gates: P6-M8
- Pro, private, and commercial features: P6-M4 or P6-M5
- Future HTML or unstructured-core upgrade: after M3, not backported into Base M3
