from __future__ import annotations

import sys
from pathlib import Path


def _bundle_root() -> Path:
    return Path(__file__).resolve().parent


def _prepend_bundle_paths(bundle_root: Path) -> None:
    package_roots = [
        bundle_root / "packages" / "zephyr-core" / "src",
        bundle_root / "packages" / "zephyr-ingest" / "src",
        bundle_root / "packages" / "uns-stream" / "src",
        bundle_root / "runner",
    ]
    for package_root in reversed(package_roots):
        sys.path.insert(0, str(package_root))


def main(argv: list[str] | None = None) -> int:
    bundle_root = _bundle_root()
    _prepend_bundle_paths(bundle_root)
    import p6_m3_public_core_local_runner as runner_module

    args = list(sys.argv[1:] if argv is None else argv)
    if "--root" not in args:
        args = ["--root", str(bundle_root), *args]
    return runner_module.main(args)


if __name__ == "__main__":
    raise SystemExit(main())
