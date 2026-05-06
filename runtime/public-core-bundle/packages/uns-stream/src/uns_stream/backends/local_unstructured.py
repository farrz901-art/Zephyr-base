from __future__ import annotations

from typing import Any, Callable

from uns_stream._internal.errors import missing_extra
from uns_stream._internal.serde import to_zephyr_elements
from zephyr_core import ErrorCode, PartitionStrategy, ZephyrElement, ZephyrError

_EXTRA_BY_KIND: dict[str, str] = {
    "text": "text",
    "md": "md",
}


def _load_partition_fn(kind: str) -> Callable[..., Any]:
    fn_name = f"partition_{kind}"

    try:
        mod = __import__(f"unstructured.partition.{kind}", fromlist=[fn_name])
        fn = getattr(mod, fn_name)
        return fn
    except ModuleNotFoundError as e:
        extra = _EXTRA_BY_KIND.get(kind, "text")
        raise missing_extra(extra=extra, detail=str(e)) from e
    except AttributeError as e:
        raise ZephyrError(
            code=ErrorCode.UNS_UNSUPPORTED_TYPE,
            message=(
                f"Unsupported kind '{kind}': missing {fn_name} in unstructured.partition.{kind}"
            ),
            details={"kind": kind, "fn_name": fn_name},
        ) from e


class LocalUnstructuredBackend:
    name = "unstructured"
    backend = "local"

    def __init__(self) -> None:
        try:
            from importlib.metadata import version

            self.version = version("unstructured")
        except Exception:
            from unstructured import __version__ as v

            self.version = getattr(v, "__version__", str(v))

    def partition_elements(
        self,
        *,
        filename: str,
        kind: str,
        strategy: PartitionStrategy,
        unique_element_ids: bool = True,
        **kwargs: Any,
    ) -> list[ZephyrElement]:
        fn = _load_partition_fn(kind)

        call_kwargs: dict[str, Any] = {
            "filename": filename,
            "unique_element_ids": unique_element_ids,
            **kwargs,
        }
        elements = fn(**call_kwargs)
        return to_zephyr_elements(elements)
