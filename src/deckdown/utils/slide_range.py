from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass


@dataclass(frozen=True)
class SlideRange:
    items: tuple[int, ...]

    def __post_init__(self) -> None:
        if any(i <= 0 for i in self.items):
            raise ValueError("Slide indices must be positive (1-based)")
        # Ensure items are strictly increasing and unique
        if any(b <= a for a, b in zip(self.items, self.items[1:], strict=False)):
            raise ValueError("Slide indices must be strictly increasing and unique")

    def __iter__(self) -> Iterator[int]:
        return iter(self.items)

    def __len__(self) -> int:  # noqa: D401 - simple length
        return len(self.items)

    def contains(self, index: int) -> bool:
        if index <= 0:
            raise ValueError("index must be positive (1-based)")
        # Binary search could be used; linear is fine for small ranges
        return index in self.items

    def as_list(self) -> list[int]:
        return list(self.items)

    @classmethod
    def from_iterable(cls, indices: Iterable[int]) -> SlideRange:
        normalized = _normalize_indices(indices)
        return cls(items=tuple(normalized))

    @classmethod
    def parse(cls, spec: str) -> SlideRange:
        return cls.from_iterable(_parse_spec(spec))


def parse_slide_range(spec: str) -> list[int]:
    return SlideRange.parse(spec).as_list()


def _normalize_indices(indices: Iterable[int]) -> list[int]:
    seen: set[int] = set()
    result: list[int] = []
    for i in indices:
        if i <= 0:
            raise ValueError("Slide indices must be positive (1-based)")
        if i not in seen:
            seen.add(i)
            result.append(i)
    result.sort()
    return result


def _parse_spec(spec: str) -> Iterator[int]:
    if spec.strip() == "":
        raise ValueError("Slide range spec cannot be empty")

    for raw in spec.split(","):
        item = raw.strip()
        if not item:
            raise ValueError("Empty item in slide range spec")
        if "-" in item:
            start_str, end_str = _split_once(item, "-")
            start = _parse_int(start_str)
            end = _parse_int(end_str)
            if start > end:
                raise ValueError(f"Invalid range '{item}': start > end")
            yield from range(start, end + 1)
        else:
            yield _parse_int(item)


def _split_once(s: str, sep: str) -> tuple[str, str]:
    left, _, right = s.partition(sep)
    if not left or not right:
        raise ValueError(f"Invalid item '{s}': expected <a>{sep}<b>")
    return left, right


def _parse_int(s: str) -> int:
    try:
        value = int(s)
    except ValueError as exc:  # pragma: no cover - error branch observable via tests
        raise ValueError(f"Invalid integer '{s}' in slide range spec") from exc
    if value <= 0:
        raise ValueError("Indices must be positive (1-based)")
    return value
