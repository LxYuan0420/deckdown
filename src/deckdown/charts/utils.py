from __future__ import annotations

from typing import Any, Iterable

from pptx.chart.data import BubbleChartData, CategoryChartData, XyChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
from pptx.dml.color import RGBColor


def map_chart_type(kind: str) -> XL_CHART_TYPE:
    t = (kind or "").lower()
    return {
        "column": XL_CHART_TYPE.COLUMN_CLUSTERED,
        "bar": XL_CHART_TYPE.BAR_CLUSTERED,
        "line": XL_CHART_TYPE.LINE,
        "pie": XL_CHART_TYPE.PIE,
        "donut": XL_CHART_TYPE.DOUGHNUT,
        "scatter": XL_CHART_TYPE.XY_SCATTER,
        "bubble": XL_CHART_TYPE.BUBBLE,
    }.get(t, XL_CHART_TYPE.COLUMN_CLUSTERED)


def build_chart_data(xl_type: XL_CHART_TYPE, series: Iterable[Any], categories: Iterable[Any]):  # noqa: ANN401
    if xl_type == XL_CHART_TYPE.XY_SCATTER:
        data = XyChartData()
        for ser in series or ():
            s = data.add_series(ser.name or "Series")
            xs = list(ser.x_values or ())
            ys = list(ser.values or ())
            for x, y in zip(xs, ys, strict=False):
                s.add_data_point(x if x is not None else 0, y if y is not None else 0)
        return data
    if xl_type == XL_CHART_TYPE.BUBBLE:
        data = BubbleChartData()
        for ser in series or ():
            s = data.add_series(ser.name or "Series")
            xs = list(ser.x_values or ())
            ys = list(ser.values or ())
            sz = list(ser.sizes or ())
            n = min(len(xs), len(ys), len(sz) if sz else len(ys))
            for i in range(n):
                s.add_data_point(xs[i] or 0, ys[i] or 0, (sz[i] or 1) if sz else 1)
        return data
    data = CategoryChartData()
    data.categories = list(categories or [])
    for ser in series or ():
        data.add_series(
            ser.name or "Series", [v if v is not None else 0 for v in (ser.values or ())]
        )
    return data


def apply_plot_area(chart: Any, plot_area: dict | None) -> None:  # noqa: ANN401
    if not plot_area:
        return
    has_labels = bool(plot_area.get("has_data_labels", False))
    if chart.plots:
        try:
            chart.plots[0].has_data_labels = has_labels
        except Exception:
            pass
    chart.has_legend = bool(plot_area.get("has_legend", False))
    pos = (plot_area.get("legend_pos") or "").lower()
    pos_map = {
        "right": XL_LEGEND_POSITION.RIGHT,
        "left": XL_LEGEND_POSITION.LEFT,
        "top": XL_LEGEND_POSITION.TOP,
        "bottom": XL_LEGEND_POSITION.BOTTOM,
    }
    if pos in pos_map:
        try:
            chart.legend.position = pos_map[pos]
        except Exception:
            pass


def apply_series_labels_and_color(plot_series: Any, ser_ast: Any) -> None:  # noqa: ANN401
    lab = getattr(ser_ast, "labels", None) or {}
    if lab:
        dl = plot_series.data_labels
        for key in ("show_value", "show_category_name", "show_series_name", "show_percentage"):
            if key in lab and lab[key] is not None:
                try:
                    setattr(dl, key, bool(lab[key]))
                except Exception:
                    pass
        if lab.get("number_format"):
            try:
                dl.number_format = str(lab["number_format"])
            except Exception:
                pass
    col = getattr(ser_ast, "color", None) or {}
    hexrgb = (col.get("resolved_rgb") or "")[1:]
    if hexrgb:
        try:
            plot_series.format.fill.solid()
            plot_series.format.fill.fore_color.rgb = RGBColor(
                int(hexrgb[0:2], 16), int(hexrgb[2:4], 16), int(hexrgb[4:6], 16)
            )
        except Exception:
            pass


def apply_point_colors(plot_series: Any, ser_ast: Any) -> None:  # noqa: ANN401
    points = getattr(ser_ast, "points", None) or []
    for meta in points:
        idx = meta.get("idx")
        col = (meta.get("color") or {}).get("resolved_rgb", None)
        if idx is None or not col:
            continue
        hexrgb = col[1:]
        try:
            pt = plot_series.points[idx]
            pt.format.fill.solid()
            pt.format.fill.fore_color.rgb = RGBColor(
                int(hexrgb[0:2], 16), int(hexrgb[2:4], 16), int(hexrgb[4:6], 16)
            )
        except Exception:
            continue


def apply_axes(chart: Any, axes: dict | None) -> None:  # noqa: ANN401
    if not axes:
        return
    if "category" in axes:
        t = axes["category"].get("title")
        if t:
            try:
                chart.category_axis.has_title = True
                chart.category_axis.axis_title.text_frame.text = str(t)
            except Exception:
                pass
    if "value" in axes:
        v = axes["value"]
        try:
            if v.get("title"):
                chart.value_axis.has_title = True
                chart.value_axis.axis_title.text_frame.text = str(v["title"])
            if v.get("min") is not None:
                chart.value_axis.minimum_scale = float(v["min"])
            if v.get("max") is not None:
                chart.value_axis.maximum_scale = float(v["max"])
            if v.get("major_unit") is not None:
                chart.value_axis.major_unit = float(v["major_unit"])
            if v.get("format_code"):
                chart.value_axis.tick_labels.number_format = str(v["format_code"])
        except Exception:
            pass
