from __future__ import annotations

from deckdown.models import Chart, ChartSeries


def test_chart_models_construct() -> None:
    s1 = ChartSeries(name="S1", values=(1.0, 2.0))
    s2 = ChartSeries(name=None, values=())
    ch = Chart(type="line", series=(s1, s2), categories=("A", "B"))

    assert ch.type == "line"
    assert len(ch.series) == 2
    assert ch.categories == ("A", "B")
