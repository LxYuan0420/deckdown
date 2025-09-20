from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final

__all__ = [
    "Deck",
    "Slide",
    "TextBlock",
    "Bullet",
    "Table",
    "Chart",
    "ChartSeries",
]


@dataclass(frozen=True)
class TextBlock:
    text: str


@dataclass(frozen=True)
class Bullet:
    level: int
    text: str

    def __post_init__(self) -> None:  # noqa: D401 - simple validation
        if self.level < 0:
            raise ValueError("bullet level must be >= 0")


@dataclass(frozen=True)
class Table:
    rows: tuple[tuple[str, ...], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        # Ensure all rows are tuples (constructor contract is tuples only)
        # and not ragged (we allow ragged tables for now; renderer will handle).
        # Keep this method for potential future shape checks.
        _ROWS_TYPE_CHECK: Final[bool] = isinstance(self.rows, tuple)  # noqa: N806
        if not _ROWS_TYPE_CHECK:
            raise TypeError("rows must be a tuple of tuple[str, ...]")


@dataclass(frozen=True)
class ChartSeries:
    name: str | None
    values: tuple[float, ...]


@dataclass(frozen=True)
class Chart:
    type: str
    series: tuple[ChartSeries, ...] = field(default_factory=tuple)
    categories: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class Slide:
    index: int
    title: str | None = None
    text_blocks: tuple[TextBlock, ...] = field(default_factory=tuple)
    bullets: tuple[Bullet, ...] = field(default_factory=tuple)
    tables: tuple[Table, ...] = field(default_factory=tuple)
    charts: tuple[Chart, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.index <= 0:
            raise ValueError("slide index must be positive (1-based)")


@dataclass(frozen=True)
class Deck:
    file: str
    title: str | None = None
    slides: tuple[Slide, ...] = field(default_factory=tuple)
