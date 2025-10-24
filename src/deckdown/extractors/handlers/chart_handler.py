from __future__ import annotations

from typing import Any, Optional

from pptx.enum.chart import XL_CHART_TYPE

from deckdown.ast import (
    CategoryAxis,
    ChartAxes,
    ChartDataLabelOptions,
    ChartDataPoint,
    ChartPayload,
    ChartShape,
    ChartSeriesModel,
    PlotAreaSpec,
    ShapeKind,
    ValueAxis,
)
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
        subtype = None
        if ctype_enum is not None:
            if ctype_enum in (
                XL_CHART_TYPE.COLUMN_CLUSTERED,
                XL_CHART_TYPE.COLUMN_STACKED,
                XL_CHART_TYPE.COLUMN_STACKED_100,
            ):
                ctype = "column"
                if ctype_enum == XL_CHART_TYPE.COLUMN_STACKED:
                    subtype = "stacked"
                elif ctype_enum == XL_CHART_TYPE.COLUMN_STACKED_100:
                    subtype = "percentStacked"
            elif ctype_enum in (
                XL_CHART_TYPE.BAR_CLUSTERED,
                XL_CHART_TYPE.BAR_STACKED,
                XL_CHART_TYPE.BAR_STACKED_100,
            ):
                ctype = "bar"
                if ctype_enum == XL_CHART_TYPE.BAR_STACKED:
                    subtype = "stacked"
                elif ctype_enum == XL_CHART_TYPE.BAR_STACKED_100:
                    subtype = "percentStacked"
            elif ctype_enum in (XL_CHART_TYPE.LINE, XL_CHART_TYPE.LINE_MARKERS):
                ctype = "line"
                if ctype_enum == XL_CHART_TYPE.LINE_MARKERS:
                    subtype = "markers"
            elif ctype_enum in (XL_CHART_TYPE.PIE, XL_CHART_TYPE.DOUGHNUT):
                ctype = "pie" if ctype_enum == XL_CHART_TYPE.PIE else "donut"
            elif ctype_enum in (XL_CHART_TYPE.XY_SCATTER,):
                ctype = "scatter"
            elif ctype_enum in (XL_CHART_TYPE.BUBBLE,):
                ctype = "bubble"
            else:
                ctype = str(ctype_enum).split(" ")[0].lower()

        plots = list(getattr(ch, "plots", ()))
        cats: list[str | float] = []
        if plots:
            try:
                raw = list(plots[0].categories)
                cats = [self._cat_value(val) for val in raw]
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
                if xvals is None:
                    x_cache = self._extract_numeric_values(getattr(ser, "_ser", None), "xVal")
                    if x_cache:
                        xvals = tuple(x_cache)
                try:
                    bs = getattr(ser, "bubble_sizes", None)
                    if bs is not None:
                        sizes = tuple(bs)
                except Exception:
                    sizes = None
                if sizes is None and ctype in ("bubble",):
                    s_cache = self._extract_numeric_values(getattr(ser, "_ser", None), "bubbleSize")
                    if s_cache:
                        sizes = tuple(s_cache)
                color = None
                try:
                    f = ser.format.fill
                    fc = getattr(f, "fore_color", None)
                    if fc is not None:
                        color = ctx.theme.color_dict_from_colorformat(fc)
                except Exception:
                    color = None
                points_meta: list[ChartDataPoint] = []
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
                            points_meta.append(ChartDataPoint(idx=idx, color=pc))
                except Exception:
                    points_meta = []
                labels = None
                try:
                    dl = getattr(ser, "data_labels", None)
                    if dl is not None:
                        labels = {}
                        for key in (
                            "show_value",
                            "show_category_name",
                            "show_series_name",
                            "show_percentage",
                        ):
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

                series_out.append(
                    ChartSeriesModel(
                        name=name,
                        values=vals,
                        color=color,
                        points=tuple(points_meta) if points_meta else None,
                        x_values=xvals,
                        sizes=sizes,
                        labels=ChartDataLabelOptions(**labels) if labels else None,
                    )
                )

        plot_area = PlotAreaSpec(
            has_data_labels=bool(getattr(plots[0], "has_data_labels", False)) if plots else None,
            has_legend=bool(getattr(ch, "has_legend", False)),
        )
        if (
            getattr(ch, "legend", None) is not None
            and getattr(ch.legend, "position", None) is not None
        ):
            plot_area = plot_area.model_copy(
                update={
                    "legend_pos": str(ch.legend.position).split(" ")[0].lower(),
                }
            )
        if not any(plot_area.model_dump(exclude_none=True).values()):
            plot_area = None

        axes_category = None
        axes_value = None
        try:
            ca = getattr(ch, "category_axis", None)
            if ca is not None and getattr(ca, "has_title", False):
                title = getattr(getattr(ca, "axis_title", None), "text_frame", None)
                if title is not None and title.text:
                    axes_category = CategoryAxis(title=str(title.text))
        except Exception:
            pass
        try:
            va = getattr(ch, "value_axis", None)
            if va is not None:
                v_args: dict[str, float | str] = {}
                try:
                    if getattr(va, "has_title", False):
                        t = getattr(getattr(va, "axis_title", None), "text_frame", None)
                        if t is not None and t.text:
                            v_args["title"] = str(t.text)
                except Exception:
                    pass
                for key, attr in (
                    ("min", "minimum_scale"),
                    ("max", "maximum_scale"),
                    ("major_unit", "major_unit"),
                ):
                    try:
                        val = getattr(va, attr)
                        if val is not None:
                            v_args[key] = float(val)
                    except Exception:
                        pass
                try:
                    fmt = getattr(getattr(va, "tick_labels", None), "number_format", None)
                    if fmt:
                        v_args["format_code"] = str(fmt)
                except Exception:
                    pass
                if v_args:
                    axes_value = ValueAxis(**v_args)
        except Exception:
            pass

        axes = None
        if axes_category or axes_value:
            axes = ChartAxes(category=axes_category, value=axes_value)

        style = None
        try:
            style_val = getattr(ch, "chart_style", None)
            if style_val is not None:
                style = int(style_val)
        except Exception:
            style = None

        return ChartShape(
            id=f"s{getattr(shape, 'shape_id', z)}",
            kind=ShapeKind.CHART,
            name=getattr(shape, "name", None),
            bbox=bbox,
            z=z,
            rotation=None,
            chart=ChartPayload(
                type=ctype or "unknown",
                subtype=subtype,
                categories=tuple(cats),
                series=tuple(series_out),
                plot_area=plot_area,
                axes=axes,
                style=style,
            ),
        )

    @staticmethod
    def _extract_numeric_values(ser_obj: Any, attr: str) -> tuple[float | None, ...] | None:  # noqa: ANN401
        if ser_obj is None:
            return None
        try:
            data_src = getattr(ser_obj, attr)
        except Exception:
            data_src = None
        if data_src is None:
            return None
        try:
            containers = list(data_src.getchildren())
        except Exception:
            return None
        values: list[float | None] = []
        for container in containers:
            tag = getattr(container, "tag", "")
            if tag.endswith("numRef"):
                cache = ChartShapeHandler._find_child(container, "numCache")
                if cache is not None:
                    values.extend(ChartShapeHandler._collect_numeric_points(cache))
            elif tag.endswith("numLit"):
                values.extend(ChartShapeHandler._collect_numeric_points(container))
        return tuple(values) if values else None

    @staticmethod
    def _find_child(node: Any, suffix: str) -> Any | None:  # noqa: ANN401
        try:
            for child in node.getchildren():
                if getattr(child, "tag", "").endswith(suffix):
                    return child
        except Exception:
            return None
        return None

    @staticmethod
    def _collect_numeric_points(container: Any) -> list[float | None]:  # noqa: ANN401
        pts: list[float | None] = []
        try:
            children = container.getchildren()
        except Exception:
            return pts
        for child in children:
            if not getattr(child, "tag", "").endswith("pt"):
                continue
            try:
                v_el = child.getchildren()[0]
                txt = getattr(v_el, "text", None)
                pts.append(float(txt) if txt is not None else None)
            except Exception:
                pts.append(None)
        return pts

    @staticmethod
    def _cat_value(val: Any) -> str | float:  # noqa: ANN401
        if hasattr(val, "label"):
            try:
                return str(val.label)
            except Exception:
                return str(val)
        return val
