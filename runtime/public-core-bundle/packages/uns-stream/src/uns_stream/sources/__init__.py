from __future__ import annotations

from uns_stream.backends.base import PartitionBackend
from uns_stream.partition.auto import partition as auto_partition
from zephyr_core import PartitionResult, PartitionStrategy


def normalize_uns_input_identity_sha(*, filename: str, default_sha: str) -> str:
    del filename
    return default_sha


def process_file(
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
    return auto_partition(
        filename=filename,
        strategy=strategy,
        unique_element_ids=unique_element_ids,
        backend=backend,
        run_id=run_id,
        pipeline_version=pipeline_version,
        sha256=sha256,
        size_bytes=size_bytes,
    )
