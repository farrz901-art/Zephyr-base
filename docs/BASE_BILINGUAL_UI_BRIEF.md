# Base Bilingual UI Brief

S16 introduces a bilingual product shell for Zephyr Base.

## Languages

- English
- 中文

## Core UX promises

- The primary action remains local processing only.
- The user can switch languages from the visible shell without reloading the app.
- Critical labels must exist in both languages:
  app title, subtitles, input labels, run buttons, status states, results, output,
  supported formats, advanced diagnostics, and user-facing failure states.

## Information architecture

- Header: product identity, language toggle, local-only/runtime badges
- Main: input, run status, result preview, output location
- Advanced: receipt, usage fact raw JSON, lineage, runtime internals, proof export,
  sample regression modes

## Capability truth

This bilingual shell does not expand runtime capability. Base still supports only:

- `.txt`
- `.text`
- `.log`
- `.md`
- `.markdown`
