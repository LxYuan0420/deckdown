from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from collections.abc import Iterable
from contextlib import suppress

from pptx import Presentation
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE, MSO_CONNECTOR_TYPE
from pptx.util import Emu

from deckdown.ast import (
    BasicShape,
    ChartShape,
    LineShape,
    PictureShape,
    SlideDoc,
    TableShape,
    TextShape,
)
from deckdown.charts.utils import (
    apply_axes,
    apply_plot_area,
    apply_point_colors,
    apply_series_labels_and_color,
    build_chart_data,
    map_chart_type,
)
from deckdown.text.emit import write_text_frame


@dataclass(frozen=True)
class DeckAssembler:
    def assemble(self, docs: Iterable[SlideDoc], *, out: Path) -> None:  # noqa: C901
        prs = Presentation()
        blank = prs.slide_layouts[6]
        # Ensure empty deck
        while len(prs.slides) > 0:
            rel_id = prs.slides._sldIdLst[0].rId  # type: ignore[attr-defined]
            prs.part.drop_rel(rel_id)
            prs.slides._sldIdLst.remove(prs.slides._sldIdLst[0])  # type: ignore[attr-defined]

        # Set deck slide size from first doc if present
        docs_list = list(docs)
        if docs_list:
            first = docs_list[0]
            with suppress(Exception):
                prs.slide_width = Emu(first.slide.size.width_emu)
                prs.slide_height = Emu(first.slide.size.height_emu)

        for doc in docs_list:
            s = prs.slides.add_slide(blank)
            # Note: slide size is a deck-level setting in PPTX; we keep default for now.
            for sh in doc.slide.shapes:
                if isinstance(sh, TextShape):
                    self._add_text(s, sh)
                elif isinstance(sh, PictureShape):
                    self._add_picture(s, sh)
                elif isinstance(sh, TableShape):
                    self._add_table(s, sh)
                elif isinstance(sh, BasicShape):
                    self._add_basic(s, sh)
                elif isinstance(sh, LineShape):
                    self._add_line(s, sh)
                elif isinstance(sh, ChartShape):
                    self._add_chart(s, sh)

        prs.save(str(out))

    # --- helpers ---
    def _add_text(self, slide, sh: TextShape) -> None:  # noqa: ANN001
        left = Emu(sh.bbox.x_emu)
        top = Emu(sh.bbox.y_emu)
        width = Emu(sh.bbox.w_emu)
        height = Emu(sh.bbox.h_emu)
        tx = slide.shapes.add_textbox(left, top, width, height)
        tf = tx.text_frame
        write_text_frame(tf, sh.text)

    def _add_picture(self, slide, sh: PictureShape) -> None:  # noqa: ANN001
        media = sh.image.media
        if not media or not media.data_url:
            return
        data_url = media.data_url
        if not data_url.startswith("data:") or ";base64," not in data_url:
            return
        b64 = data_url.split(",", 1)[1]
        try:
            data = BytesIO(__import__("base64").b64decode(b64))
            data.seek(0)
        except Exception:
            return
        left = Emu(sh.bbox.x_emu)
        top = Emu(sh.bbox.y_emu)
        width = Emu(sh.bbox.w_emu)
        height = Emu(sh.bbox.h_emu)
        slide.shapes.add_picture(data, left, top, width=width, height=height)

    def _add_table(self, slide, sh: TableShape) -> None:  # noqa: ANN001
        left = Emu(sh.bbox.x_emu)
        top = Emu(sh.bbox.y_emu)
        width = Emu(sh.bbox.w_emu)
        height = Emu(sh.bbox.h_emu)
        rows, cols = sh.table.rows, sh.table.cols
        t = slide.shapes.add_table(rows, cols, left, top, width, height).table
        # Initialize with empty strings
        for r in range(rows):
            for c in range(cols):
                t.cell(r, c).text = ""
        # Apply merges and set text on top-left cells
        for cell in sh.table.cells:
            r, c = cell.r, cell.c
            rr = r + max(1, cell.rowspan) - 1
            cc = c + max(1, cell.colspan) - 1
            if rr > r or cc > c:
                with suppress(Exception):
                    t.cell(r, c).merge(t.cell(rr, cc))
            # write text
            tf = t.cell(r, c).text_frame
            write_text_frame(tf, cell.text)

    def _add_basic(self, slide, sh: BasicShape) -> None:  # noqa: ANN001,C901
        left = Emu(sh.bbox.x_emu)
        top = Emu(sh.bbox.y_emu)
        width = Emu(sh.bbox.w_emu)
        height = Emu(sh.bbox.h_emu)
        geom_map = {
            "rectangle": MSO_AUTO_SHAPE_TYPE.RECTANGLE,
            "rounded rectangle": MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE,
            "roundrect": MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE,
            "ellipse": MSO_AUTO_SHAPE_TYPE.OVAL,
            "oval": MSO_AUTO_SHAPE_TYPE.OVAL,
        }
        kind = geom_map.get((sh.geom or "").lower(), MSO_AUTO_SHAPE_TYPE.RECTANGLE)
        shp = slide.shapes.add_shape(kind, left, top, width, height)
        # text
        if sh.text and sh.text.paras:
            tf = shp.text_frame
            write_text_frame(tf, sh.text)
        # style (fill only; stroke best-effort)
        with suppress(Exception):
            if (
                sh.style
                and sh.style.fill
                and sh.style.fill.color
                and sh.style.fill.color.get("resolved_rgb")
            ):
                shp.fill.solid()
                from pptx.dml.color import RGBColor

                rgb = sh.style.fill.color["resolved_rgb"][1:]
                shp.fill.fore_color.rgb = RGBColor(
                    int(rgb[0:2], 16), int(rgb[2:4], 16), int(rgb[4:6], 16)
                )

    def _add_line(self, slide, sh: LineShape) -> None:  # noqa: ANN001
        x1 = Emu(sh.bbox.x_emu)
        y1 = Emu(sh.bbox.y_emu)
        x2 = Emu(sh.bbox.x_emu + sh.bbox.w_emu)
        y2 = Emu(sh.bbox.y_emu + sh.bbox.h_emu)
        slide.shapes.add_connector(MSO_CONNECTOR_TYPE.STRAIGHT, x1, y1, x2, y2)

    def _add_chart(self, slide, sh: ChartShape) -> None:  # noqa: ANN001
        xl_type = map_chart_type(sh.chart.type or "")
        data = build_chart_data(xl_type, sh.chart.series or (), sh.chart.categories or [])

        left = Emu(sh.bbox.x_emu)
        top = Emu(sh.bbox.y_emu)
        width = Emu(sh.bbox.w_emu)
        height = Emu(sh.bbox.h_emu)
        chart = slide.shapes.add_chart(xl_type, left, top, width, height, data).chart

        apply_plot_area(chart, sh.chart.plot_area or {})
        plots = chart.plots
        if not plots:
            return
        plot0 = plots[0]

        for idx, ser in enumerate(sh.chart.series or ()):
            series_obj = plot0.series[idx]
            apply_series_labels_and_color(series_obj, ser)
            apply_point_colors(series_obj, ser)

        apply_axes(chart, sh.chart.axes or {})
