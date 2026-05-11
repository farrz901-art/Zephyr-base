# Base external UX smoke policy

S17 validates the portable package from an external user-facing perspective.

This proof path is not a signed installer, not an official release, and not a full
installer UX claim.

S17 validates this flow:
- unpack the portable package from an external directory
- launch the Base app from that external directory
- switch between English and 中文
- run pasted local text
- run a supported local file
- confirm normalized preview and output location are visible
- confirm Advanced is collapsed by default
- expand Advanced and confirm receipt, evidence, usage fact, lineage, and proof export

Runtime and product truth remain unchanged:
- local-only
- no login
- no network at runtime
- no billing semantics
- no Pro, Web-core, private core, or commercial logic
- supported formats remain .txt, .text, .log, .md, and .markdown

S17 can only be sealed when a real manual GUI proof or a future semiautomated external GUI
proof is imported and validated. Runtime smoke from an extracted package is necessary but not
sufficient for sealing the full external UX claim.
