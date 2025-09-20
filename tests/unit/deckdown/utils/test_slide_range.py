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
    with pytest.raises(ValueError):
        _ = sr.contains(0)


def test_slide_range_dunder_len_and_iter_and_invalid_items() -> None:
    # __len__ and __iter__
    sr = SlideRange(items=(1, 3, 5))
    assert len(sr) == 3
    assert list(iter(sr)) == [1, 3, 5]
    # Invalid: non-positive items
    with pytest.raises(ValueError):
        _ = SlideRange(items=(0,))
    # Invalid: not strictly increasing
    with pytest.raises(ValueError):
        _ = SlideRange(items=(1, 1))
    with pytest.raises(ValueError):
        _ = SlideRange(items=(2, 1))


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


def test_normalize_indices_negative_raises() -> None:
    # Covers the error branch in _normalize_indices
    with pytest.raises(ValueError):
        _ = SlideRange.from_iterable([1, -1, 2])
