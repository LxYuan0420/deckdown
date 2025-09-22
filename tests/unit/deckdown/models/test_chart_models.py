from __future__ import annotations

from deckdown.models import Chart, ChartSeries


class TestChartModels:
    def test_construct(self) -> None:
        # Arrange
        s1 = ChartSeries(name="S1", values=(1.0, 2.0))
        s2 = ChartSeries(name=None, values=())
        # Act
        ch = Chart(type="line", series=(s1, s2), categories=("A", "B"))
        # Assert
        assert ch.type == "line"
        assert len(ch.series) == 2
        assert ch.categories == ("A", "B")
