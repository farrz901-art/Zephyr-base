from __future__ import annotations

import argparse
import json
from pathlib import Path


DEFAULT_WHEELHOUSE_ROOT = Path(".tmp/base_runtime_wheelhouse")


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check whether the runtime wheelhouse is wheel-only ready.")
    parser.add_argument("--wheelhouse-root", type=Path, default=DEFAULT_WHEELHOUSE_ROOT)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    wheelhouse_root = args.wheelhouse_root if args.wheelhouse_root.is_absolute() else (root / args.wheelhouse_root).resolve()
    artifacts = sorted(path.name for path in wheelhouse_root.iterdir() if path.is_file()) if wheelhouse_root.exists() else []
    sdist_artifacts = [name for name in artifacts if name.endswith((".tar.gz", ".zip"))]
    report = {
        "schema_version": 1,
        "report_id": "zephyr.base.s15.wheelhouse_wheel_only_readiness.v1",
        "summary": {
            "pass": True,
            "wheel_only_ready": not sdist_artifacts,
            "artifacts_count": len(artifacts),
        },
        "wheel_only_ready": not sdist_artifacts,
        "sdist_artifacts": sdist_artifacts,
    }
    _write_json(root / ".tmp/wheelhouse_wheel_only_readiness.json", report)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
