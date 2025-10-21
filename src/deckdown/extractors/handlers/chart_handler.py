from __future__ import annotations

from typing import Any, Optional

from pptx.enum.chart import XL_CHART_TYPE

from deckdown.ast import ChartPayload, ChartShape, ChartSeriesModel, ShapeKind
from deckdown.extractors.context import ExtractContext
from deckdown.extractors.handlers.base import ShapeHandler


class ChartShapeHandler(ShapeHandler):
    def supports(self, shape: Any) -> bool:  # noqa: ANN401
        return bool(getattr(shape, "has_chart", False))

    def build(self, shape: Any, *, z: int, ctx: ExtractContext) -> Optional[ChartShape]:  # noqa: ANN401
        bbox = ctx.bbox(
            left_emu=int(getattr(shape, "left", 0)),
            top_emu=int(getattr(shape, "top", 0)),
            width_emu=int(getattr(shape, "width", 0)),
            height_emu=int(getattr(shape, "height", 0)),
        )
        ch = shape.chart
        ctype_enum = getattr(ch, "chart_type", None)
        ctype = None
        if ctype_enum is not None:
            if ctype_enum in (XL_CHART_TYPE.COLUMN_CLUSTERED, XL_CHART_TYPE.COLUMN_STACKED, XL_CHART_TYPE.COLUMN_STACKED_100):
                ctype = "column"
            elif ctype_enum in (XL_CHART_TYPE.BAR_CLUSTERED, XL_CHART_TYPE.BAR_STACKED, XL_CHART_TYPE.BAR_STACKED_100):
                ctype = "bar"
            elif ctype_enum in (XL_CHART_TYPE.LINE, XL_CHART_TYPE.LINE_MARKERS):
                ctype = "line"
            elif ctype_enum in (XL_CHART_TYPE.PIE, XL_CHART_TYPE.DOUGHNUT):
                ctype = "pie" if ctype_enum == XL_CHART_TYPE.PIE else "donut"
            elif ctype_enum in (XL_CHART_TYPE.XY_SCATTER,):
                ctype = "scatter"
            elif ctype_enum in (XL_CHART_TYPE.BUBBLE,):
                ctype = "bubble"
            else:
                ctype = str(ctype_enum).split(" ")[0].lower()

        plots = list(ch.plots)
        cats: list[str | float] = []
        if plots:
            try:
                cats = list(plots[0].categories)
            except Exception:
                cats = []

        series_out: list[ChartSeriesModel] = []
        if plots:
            for ser in plots[0].series:
                name = getattr(ser, "name", None)
                vals = tuple(getattr(ser, "values", ()) or ())
                xvals = None
                sizes = None
                # scatter/bubble carry x and sizes
                try:
                    xv = getattr(ser, "x_values", None)
                    if xv is not None:
                        xvals = tuple(xv)
                except Exception:
                    xvals = None
                try:
                    bs = getattr(ser, "bubble_sizes", None)
                    if bs is not None:
                        sizes = tuple(bs)
                except Exception:
                    sizes = None
                color = None
                try:
                    f = ser.format.fill
                    fc = getattr(f, "fore_color", None)
                    if fc is not None:
                        color = ctx.theme.color_dict_from_colorformat(fc)
                except Exception:
                    color = None
                points_meta = []
                try:
                    for idx, pt in enumerate(ser.points):
                        pc = None
                        try:
                            fc = getattr(getattr(pt.format, "fill", None), "fore_color", None)
                            if fc is not None:
                                pc = ctx.theme.color_dict_from_colorformat(fc)
                        except Exception:
                            pc = None
                        if pc:
                            points_meta.append({"idx": idx, "color": pc})
                except Exception:
                    points_meta = []
                labels = None
                try:
                    dl = getattr(ser, "data_labels", None)
                    if dl is not None:
                        labels = {}
                        for key in ("show_value", "show_category_name", "show_series_name", "show_percentage"):
                            try:
                                val = getattr(dl, key)
                                if val is not None:
                                    labels[key] = bool(val)
                            except Exception:
                                pass
                        try:
                            pos = getattr(dl, "position", None)
                            if pos is not None:
                                labels["position"] = str(pos).split(" ")[0].lower()
                        except Exception:
                            pass
                        try:
                            fmt = getattr(dl, "number_format", None)
                            if fmt:
                                labels["number_format"] = str(fmt)
                        except Exception:
                            pass
                        if not labels:
                            labels = None
                except Exception:
                    labels = None

                series_out.append(ChartSeriesModel(name=name, values=vals, color=color, points=tuple(points_meta) if points_meta else None, x_values=xvals, sizes=sizes, labels=labels))

        plot_area = {
            "has_data_labels": bool(getattr(plots[0], "has_data_labels", False)) if plots else False,
            "has_legend": bool(getattr(ch, "has_legend", False)),
        }
        if getattr(ch, "legend", None) is not None and getattr(ch.legend, "position", None) is not None:
            plot_area["legend_pos"] = str(ch.legend.position).split(" ")[0].lower()

        axes = {}
        try:
            ca = getattr(ch, "category_axis", None)
            if ca is not None and getattr(ca, "has_title", False):
                title = getattr(getattr(ca, "axis_title", None), "text_frame", None)
                if title is not None and title.text:
                    axes.setdefault("category", {})["title"] = str(title.text)
        except Exception:
            pass
        try:
            va = getattr(ch, "value_axis", None)
            if va is not None:
                vdict = {}
                try:
                    if getattr(va, "has_title", False):
                        t = getattr(getattr(va, "axis_title", None), "text_frame", None)
                        if t is not None and t.text:
                            vdict["title"] = str(t.text)
                except Exception:
                    pass
                for key, attr in ("min", "minimum_scale"), ("max", "maximum_scale"), ("major_unit", "major_unit"):
                    try:
                        val = getattr(va, attr)
                        if val is not None:
                            vdict[key] = float(val)
                    except Exception:
                        pass
                try:
                    fmt = getattr(getattr(va, "tick_labels", None), "number_format", None)
                    if fmt:
                        vdict["format_code"] = str(fmt)
                except Exception:
                    pass
                if vdict:
                    axes["value"] = vdict
        except Exception:
            pass

        return ChartShape(
            id=f"s{getattr(shape, 'shape_id', z)}",
            kind=ShapeKind.CHART,
            name=getattr(shape, "name", None),
            bbox=bbox,
            z=z,
            rotation=None,
            chart=ChartPayload(type=ctype or "unknown", categories=tuple(cats), series=tuple(series_out), plot_area=plot_area, axes=axes or None),
        )
