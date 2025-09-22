from __future__ import annotations

import pytest

from deckdown.utils.slide_range import SlideRange, parse_slide_range


class TestSlideRange:
    def test_parse_basic(self) -> None:
        # Arrange/Act
        result = parse_slide_range("1-3,5,2")
        # Assert
        assert result == [1, 2, 3, 5]

    def test_from_iterable_and_contains(self) -> None:
        # Arrange
        sr = SlideRange.from_iterable([3, 1, 2, 2])
        # Act/Assert
        assert sr.as_list() == [1, 2, 3]
        assert sr.contains(1) is True
        assert sr.contains(4) is False
        with pytest.raises(ValueError):
            _ = sr.contains(0)

    def test_dunder_len_iter_and_invalid_items(self) -> None:
        # Arrange
        sr = SlideRange(items=(1, 3, 5))
        # Act/Assert
        assert len(sr) == 3
        assert list(iter(sr)) == [1, 3, 5]
        with pytest.raises(ValueError):
            _ = SlideRange(items=(0,))
        with pytest.raises(ValueError):
            _ = SlideRange(items=(1, 1))
        with pytest.raises(ValueError):
            _ = SlideRange(items=(2, 1))

    @pytest.mark.parametrize("bad", ["", "0", "1-0", "5-3", "a", "1-", "-3", ","])
    def test_parse_invalid(self, bad: str) -> None:
        # Arrange/Act/Assert
        with pytest.raises(ValueError):
            _ = parse_slide_range(bad)

    def test_normalize_indices_negative_raises(self) -> None:
        # Arrange/Act/Assert
        with pytest.raises(ValueError):
            _ = SlideRange.from_iterable([1, -1, 2])
