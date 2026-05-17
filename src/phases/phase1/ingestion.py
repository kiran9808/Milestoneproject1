"""Download / stream the Hugging Face dataset (Phase 1 ingestion)."""

from __future__ import annotations

from typing import Any, Iterator

from .config import HF_DATASET_NAME, HF_DEFAULT_SPLIT


def iter_hf_rows(
    dataset_name: str | None = None,
    split: str | None = None,
    *,
    revision: str | None = None,
    streaming: bool = False,
) -> Iterator[dict[str, Any]]:
    """
    Yield raw row dicts from the configured Hugging Face dataset.

    Requires the `datasets` package and network on first download unless cached.
    """
    from datasets import load_dataset  # lazy import

    name = dataset_name or HF_DATASET_NAME
    sp = split or HF_DEFAULT_SPLIT
    kwargs: dict[str, Any] = {"split": sp}
    if revision is not None:
        kwargs["revision"] = revision
    if streaming:
        kwargs["streaming"] = True

    ds = load_dataset(name, **kwargs)
    if streaming:
        for row in ds:
            yield dict(row)
        return

    for i in range(len(ds)):
        yield dict(ds[i])


def row_count_estimate(
    dataset_name: str | None = None,
    split: str | None = None,
    *,
    revision: str | None = None,
) -> int:
    """Number of rows (loads metadata; non-streaming split)."""
    from datasets import load_dataset

    name = dataset_name or HF_DATASET_NAME
    sp = split or HF_DEFAULT_SPLIT
    kwargs: dict[str, Any] = {"split": sp}
    if revision is not None:
        kwargs["revision"] = revision
    ds = load_dataset(name, **kwargs)
    return len(ds)
