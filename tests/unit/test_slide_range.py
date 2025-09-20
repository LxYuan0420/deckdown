from __future__ import annotations

import pytest

from deckdown.utils.slide_range import SlideRange, parse_slide_range


def test_parse_slide_range_basic() -> None:
    assert parse_slide_range("1-3,5,2") == [1, 2, 3, 5]


def test_slide_range_from_iterable_and_contains() -> None:
    sr = SlideRange.from_iterable([3, 1, 2, 2])
    assert sr.as_list() == [1, 2, 3]
    assert sr.contains(1) is True
    assert sr.contains(4) is False


@pytest.mark.parametrize(
    "bad",
    [
        "",
        "0",
        "1-0",
        "5-3",
        "a",
        "1-",
        "-3",
        ",",
    ],
)
def test_parse_slide_range_invalid(bad: str) -> None:
    with pytest.raises(ValueError):
        _ = parse_slide_range(bad)
