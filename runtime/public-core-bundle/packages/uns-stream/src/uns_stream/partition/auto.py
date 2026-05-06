from __future__ import annotations

from pathlib import Path

from uns_stream.backends.base import PartitionBackend
from uns_stream.service import partition_file
from zephyr_core import ErrorCode, PartitionResult, PartitionStrategy, ZephyrError

_KIND_BY_EXT: dict[str, str] = {
    ".txt": "text",
    ".text": "text",
    ".log": "text",
    ".md": "md",
    ".markdown": "md",
}


def partition(
    *,
    filename: str,
    strategy: PartitionStrategy = PartitionStrategy.AUTO,
    unique_element_ids: bool = True,
    backend: PartitionBackend | None = None,
    run_id: str | None = None,
    pipeline_version: str | None = None,
    sha256: str | None = None,
    size_bytes: int | None = None,
) -> PartitionResult:
    ext = Path(filename).suffix.lower()
    kind = _KIND_BY_EXT.get(ext)
    if kind is None:
        raise ZephyrError(
            code=ErrorCode.UNS_UNSUPPORTED_TYPE,
            message=f"Unsupported file extension: {ext}",
            details={"filename": filename, "ext": ext},
        )

    return partition_file(
        filename=filename,
        kind=kind,
        strategy=strategy,
        unique_element_ids=unique_element_ids,
        backend=backend,
        run_id=run_id,
        pipeline_version=pipeline_version,
        sha256=sha256,
        size_bytes=size_bytes,
    )
