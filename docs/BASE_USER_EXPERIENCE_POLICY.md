# Base User Experience Policy

Zephyr Base is a free local desktop product for text and Markdown-class processing.

## Default user path

1. Choose input / 选择输入
2. Run / 开始处理
3. View result / 查看结果
4. Open output / 打开输出

## Product-shell rules

- Default copy must speak to normal users rather than engineering reviewers.
- The main surface should focus on choosing input, running locally, and reading the result.
- Advanced / Diagnostics can surface evidence, receipt, usage fact raw JSON, lineage,
  proof export, and runtime internals.
- English and Chinese language switching is part of the minimum S16 UX gate.
- The shell must keep the current Base runtime truth visible:
  local-only, no login, no billing semantics, no network runtime, and filesystem outputs.

## Boundary truth

The S16 shell must not claim:

- PDF, DOCX, image, or OCR support
- cloud processing or web/API processing
- Pro, Web-core, or private-core capability
- account, license, entitlement, payment, billing plan, or quota workflows
- signed installer, official release, or auto-update status

## Advanced-only surfaces

The following can remain available, but should be collapsed or demoted by default:

- evidence details
- receipt details
- usage fact raw JSON
- lineage and runtime internals
- sample artifact modes
- interaction proof export
