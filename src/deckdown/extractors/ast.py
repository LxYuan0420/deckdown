from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Any

from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.enum.chart import XL_CHART_TYPE
from pptx.oxml.ns import qn

from deckdown.ast import (
    BBox,
    Media,
    Paragraph,
    PicturePayload,
    PictureShape,
    ChartPayload,
    ChartShape,
    ChartSeriesModel,
    BasicStyle,
    FillSpec,
    StrokeSpec,
    BasicShape,
    LineShape,
    TableCell,
    TablePayload,
    TableShape,
    Shape,
    ShapeKind,
    SlideDoc,
    SlideModel,
    SlideSize,
    TextPayload,
    TextRun,
    TextShape,
)


EMU_PER_INCH = 914400


def _norm(v: int, denom: int) -> float:
    if denom <= 0:
        return 0.0
    return round(float(v) / float(denom), 6)


def _align_to_str(align: Any) -> str | None:  # noqa: ANN401
    try:
        name = align._member_name_  # type: ignore[attr-defined]
    except Exception:  # pragma: no cover - defensive
        return None
    m = name.lower()
    if m in {"left", "center", "right", "justify"}:
        return m
    return None


def _color_from_fill(fill: Any) -> dict | None:  # noqa: ANN401
    try:
        fc = getattr(fill, "fore_color", None)
        rgb = getattr(fc, "rgb", None)
        if rgb is not None:
            return {"resolved_rgb": f"#{str(rgb)}"}
    except Exception:
        return None
    return None


def _basic_style(shp: Any) -> BasicStyle | None:  # noqa: ANN401
    try:
        fill_color = _color_from_fill(getattr(shp, "fill", None))
        line = getattr(shp, "line", None)
        stroke_color = None
        width_pt = None
        dash = None
        if line is not None:
            try:
                stroke_color = _color_from_fill(getattr(line, "fill", None))
            except Exception:
                pass
            try:
                if getattr(line, "width", None) is not None:
                    width_pt = round(float(line.width.pt), 2)  # type: ignore[union-attr]
            except Exception:
                pass
        if fill_color or stroke_color or width_pt:
            return BasicStyle(
                fill=FillSpec(color=fill_color) if fill_color else None,
                stroke=StrokeSpec(color=stroke_color, width_pt=width_pt, dash=dash),
            )
    except Exception:
        return None
    return None


@dataclass(frozen=True)
class AstExtractor:
    def extract(self, prs: Any) -> dict[int, SlideDoc]:  # noqa: ANN401
        width = int(getattr(prs, "slide_width"))
        height = int(getattr(prs, "slide_height"))
        size = SlideSize(width_emu=width, height_emu=height)
        out: dict[int, SlideDoc] = {}
        for idx, slide in enumerate(prs.slides, start=1):
            shapes: list[Shape] = []
            for z, shp in enumerate(slide.shapes):
                # geometry
                left = int(getattr(shp, "left", 0))
                top = int(getattr(shp, "top", 0))
                w = int(getattr(shp, "width", 0))
                h = int(getattr(shp, "height", 0))
                bbox = BBox(
                    x_emu=left,
                    y_emu=top,
                    w_emu=w,
                    h_emu=h,
                    x_norm=_norm(left, width),
                    y_norm=_norm(top, height),
                    w_norm=_norm(w, width),
                    h_norm=_norm(h, height),
                )
                name = getattr(shp, "name", None)
                rot = None
                try:
                    rot = float(getattr(shp, "rotation"))  # type: ignore[arg-type]
                except Exception:  # pragma: no cover - not all shapes support rotation
                    rot = None

                # generic text shapes (non-auto shapes/lines/tables/pictures/charts)
                if getattr(shp, "has_text_frame", False) and getattr(shp, "shape_type", None) not in (
                    MSO_SHAPE_TYPE.AUTO_SHAPE,
                    MSO_SHAPE_TYPE.TABLE,
                    MSO_SHAPE_TYPE.LINE,
                ):
                    paras = []
                    try:
                        for p in shp.text_frame.paragraphs:
                            runs = []
                            for r in p.runs:
                                font = {}
                                f = r.font
                                if f is not None and f.size is not None:
                                    try:
                                        font["size_pt"] = round(float(f.size.pt), 2)  # type: ignore[union-attr]
                                    except Exception:  # pragma: no cover - safety
                                        pass
                                if f is not None and f.name:
                                    font["family"] = f.name
                                if f is not None and f.bold is not None:
                                    font["bold"] = bool(f.bold)
                                if f is not None and f.italic is not None:
                                    font["italic"] = bool(f.italic)
                                if f is not None and f.underline is not None:
                                    font["underline"] = bool(f.underline)
                                if f is not None and f.color is not None and getattr(f.color, "rgb", None):
                                    rgb = str(f.color.rgb)
                                    if len(rgb) == 6:
                                        font["color"] = {"resolved_rgb": f"#{rgb}"}
                                runs.append(TextRun(text=r.text or "", font=font or None))
                            paras.append(
                                Paragraph(
                                    lvl=int(getattr(p, "level", 0) or 0),
                                    align=_align_to_str(getattr(p, "alignment", None)),
                                    runs=tuple(runs),
                                )
                            )
                    except Exception:  # pragma: no cover - defensive
                        paras = []

                    shapes.append(
                        TextShape(
                            id=f"s{getattr(shp, 'shape_id', z)}",
                            kind=ShapeKind.TEXT,
                            name=name,
                            bbox=bbox,
                            z=z,
                            rotation=rot,
                            text=TextPayload(paras=tuple(paras)),
                        )
                    )
                    continue

                # pictures
                try:
                    if getattr(shp, "shape_type", None) == MSO_SHAPE_TYPE.PICTURE:  # type: ignore[attr-defined]
                        blob = getattr(shp.image, "blob", None)
                        content_type = getattr(shp.image, "content_type", "application/octet-stream")
                        data_url = None
                        if blob:
                            b64 = base64.b64encode(blob).decode("ascii")
                            data_url = f"data:{content_type};base64,{b64}"

                        # Cropping (fractions 0..1) if non-zero
                        crop_dict: dict[str, float] = {}
                        try:
                            cl = float(getattr(shp, "crop_left", 0.0) or 0.0)
                            cr = float(getattr(shp, "crop_right", 0.0) or 0.0)
                            ct = float(getattr(shp, "crop_top", 0.0) or 0.0)
                            cb = float(getattr(shp, "crop_bottom", 0.0) or 0.0)
                            if any(v != 0.0 for v in (cl, cr, ct, cb)):
                                crop_dict = {"left": cl, "right": cr, "top": ct, "bottom": cb}
                        except Exception:  # pragma: no cover - defensive
                            crop_dict = {}

                        alt = None
                        try:
                            alt = getattr(shp, "alternative_text", None)
                            if alt:
                                alt = str(alt)
                        except Exception:  # pragma: no cover
                            alt = None

                        payload = PicturePayload(
                            media=Media(data_url=data_url),
                            crop=crop_dict or None,
                            opacity=None,
                            alt=alt,
                        )
                        shapes.append(
                            PictureShape(
                                id=f"s{getattr(shp, 'shape_id', z)}",
                                kind=ShapeKind.PICTURE,
                                name=name,
                                bbox=bbox,
                                z=z,
                                rotation=rot,
                                image=payload,
                            )
                        )
                        continue
                except Exception:  # pragma: no cover - defensive
                    pass

                # tables
                try:
                    if getattr(shp, "shape_type", None) == MSO_SHAPE_TYPE.TABLE and getattr(shp, "has_table", False):  # type: ignore[attr-defined]
                        tbl = shp.table
                        n_rows = len(tbl.rows)
                        n_cols = len(tbl.columns)

                        # Pre-scan for merges using attributes on a:tc: rowSpan/gridSpan; vMerge/hMerge present on continued cells
                        colspans = [[1 for _ in range(n_cols)] for _ in range(n_rows)]
                        rowspans = [[1 for _ in range(n_cols)] for _ in range(n_rows)]
                        hmerge = [[False for _ in range(n_cols)] for _ in range(n_rows)]
                        vmerge = [[False for _ in range(n_cols)] for _ in range(n_rows)]
                        for r in range(n_rows):
                            for c in range(n_cols):
                                tc = tbl.cell(r, c)._tc
                                # Top-left cell carries spans
                                try:
                                    gs = tc.get("{%s}gridSpan" % qn("a:tc").partition("}")[0][1:])  # not reliable
                                except Exception:
                                    gs = None
                                # Simpler: direct attribute access
                                gs = tc.get("gridSpan") or gs
                                rs = tc.get("rowSpan")
                                hm = tc.get("hMerge")
                                vm = tc.get("vMerge")
                                if gs:
                                    try:
                                        colspans[r][c] = max(1, int(gs))
                                    except Exception:
                                        pass
                                if rs:
                                    try:
                                        rowspans[r][c] = max(1, int(rs))
                                    except Exception:
                                        pass
                                if hm:
                                    hmerge[r][c] = True
                                if vm:
                                    vmerge[r][c] = True

                        visited: set[tuple[int, int]] = set()
                        cells: list[Shape] = []

                        def cell_text_payload(_cell: Any) -> TextPayload:
                            paras = []
                            try:
                                tf = _cell.text_frame
                                for p in tf.paragraphs:
                                    runs = [TextRun(text=(r.text or "")) for r in p.runs]
                                    paras.append(Paragraph(lvl=int(getattr(p, "level", 0) or 0), runs=tuple(runs)))
                            except Exception:  # pragma: no cover
                                pass
                            return TextPayload(paras=tuple(paras))

                        table_cells: list[TableCell] = []
                        for r in range(n_rows):
                            for c in range(n_cols):
                                if (r, c) in visited:
                                    continue
                                # Skip cells that are marked as continued merges
                                if hmerge[r][c] or vmerge[r][c]:
                                    continue
                                rowspan = max(1, rowspans[r][c])
                                colspan = max(1, colspans[r][c])
                                # Mark covered cells as visited
                                for rr in range(r, min(r + rowspan, n_rows)):
                                    for cc in range(c, min(c + colspan, n_cols)):
                                        if rr == r and cc == c:
                                            continue
                                        visited.add((rr, cc))

                                tp = cell_text_payload(tbl.cell(r, c))
                                table_cells.append(
                                    TableCell(r=r, c=c, rowspan=rowspan, colspan=colspan, text=tp)
                                )

                        shapes.append(
                            TableShape(
                                id=f"s{getattr(shp, 'shape_id', z)}",
                                kind=ShapeKind.TABLE,
                                name=name,
                                bbox=bbox,
                                z=z,
                                rotation=rot,
                                table=TablePayload(rows=n_rows, cols=n_cols, cells=tuple(table_cells)),
                            )
                        )
                        continue
                except Exception:  # pragma: no cover - defensive
                    pass

                # charts (core category charts)
                try:
                    if hasattr(shp, "has_chart") and getattr(shp, "has_chart"):
                        ch = shp.chart
                        ctype_enum = getattr(ch, "chart_type", None)
                        ctype = None
                        if ctype_enum is not None:
                            # map broad families
                            if ctype_enum in (XL_CHART_TYPE.COLUMN_CLUSTERED, XL_CHART_TYPE.COLUMN_STACKED, XL_CHART_TYPE.COLUMN_STACKED_100):
                                ctype = "column"
                            elif ctype_enum in (XL_CHART_TYPE.BAR_CLUSTERED, XL_CHART_TYPE.BAR_STACKED, XL_CHART_TYPE.BAR_STACKED_100):
                                ctype = "bar"
                            elif ctype_enum in (XL_CHART_TYPE.LINE, XL_CHART_TYPE.LINE_MARKERS):
                                ctype = "line"
                            elif ctype_enum in (XL_CHART_TYPE.PIE, XL_CHART_TYPE.DOUGHNUT):
                                ctype = "pie" if ctype_enum == XL_CHART_TYPE.PIE else "donut"
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
                                color = None
                                try:
                                    f = ser.format.fill
                                    rgb = getattr(getattr(f, "fore_color", None), "rgb", None)
                                    if rgb is not None:
                                        color = {"resolved_rgb": f"#{str(rgb)}"}
                                except Exception:
                                    color = None
                                series_out.append(ChartSeriesModel(name=name, values=vals, color=color))

                        plot_area = {
                            "has_data_labels": bool(getattr(plots[0], "has_data_labels", False)) if plots else False,
                            "has_legend": bool(getattr(ch, "has_legend", False)),
                        }
                        if getattr(ch, "legend", None) is not None and getattr(ch.legend, "position", None) is not None:
                            plot_area["legend_pos"] = str(ch.legend.position).split(" ")[0].lower()

                        shapes.append(
                            ChartShape(
                                id=f"s{getattr(shp, 'shape_id', z)}",
                                kind=ShapeKind.CHART,
                                name=name,
                                bbox=bbox,
                                z=z,
                                rotation=rot,
                                chart=ChartPayload(type=ctype or "unknown", categories=tuple(cats), series=tuple(series_out), plot_area=plot_area),
                            )
                        )
                        continue
                except Exception:  # pragma: no cover - defensive
                    pass

                # basic shapes and lines
                try:
                    st = getattr(shp, "shape_type", None)
                    # auto shapes
                    if st == MSO_SHAPE_TYPE.AUTO_SHAPE:
                        geom = str(getattr(getattr(shp, "auto_shape_type", None), "name", None) or "autoShape").lower()
                        style = _basic_style(shp)
                        text_payload = None
                        if getattr(shp, "has_text_frame", False):
                            # reuse paragraph extraction for shapes with text
                            paras = []
                            try:
                                for p in shp.text_frame.paragraphs:
                                    runs = [TextRun(text=(r.text or "")) for r in p.runs]
                                    paras.append(Paragraph(lvl=int(getattr(p, "level", 0) or 0), runs=tuple(runs)))
                            except Exception:
                                pass
                            text_payload = TextPayload(paras=tuple(paras))
                        shapes.append(
                            BasicShape(
                                id=f"s{getattr(shp, 'shape_id', z)}",
                                kind=ShapeKind.BASIC,
                                name=name,
                                bbox=bbox,
                                z=z,
                                rotation=rot,
                                geom=geom,
                                style=style,
                                text=text_payload,
                            )
                        )
                        continue
                    # lines
                    if st == MSO_SHAPE_TYPE.LINE:
                        style = _basic_style(shp)
                        shapes.append(
                            LineShape(
                                id=f"s{getattr(shp, 'shape_id', z)}",
                                kind=ShapeKind.LINE,
                                name=name,
                                bbox=bbox,
                                z=z,
                                rotation=rot,
                                style=style,
                            )
                        )
                        continue
                except Exception:
                    pass

                # Other kinds (groups) will arrive in later milestones

            slide_model = SlideModel(index=idx, size=size, shapes=tuple(shapes))
            out[idx] = SlideDoc(slide=slide_model)
        return out
