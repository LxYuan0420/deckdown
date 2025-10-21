from __future__ import annotations

import html
from dataclasses import dataclass

from deckdown.ast import SlideDoc


EMU_PER_INCH = 914400
DPI = 96.0


def emu_to_px(v_emu: int) -> int:
    return int(round((v_emu / EMU_PER_INCH) * DPI))


@dataclass(frozen=True)
class HtmlPreviewRenderer:
    def render_slide(self, doc: SlideDoc) -> str:
        s = doc.slide
        wpx = emu_to_px(s.size.width_emu)
        hpx = emu_to_px(s.size.height_emu)
        out: list[str] = []
        out.append(f'<div class="slide" style="position:relative;width:{wpx}px;height:{hpx}px;border:1px solid #ddd;margin:16px auto;">')
        for sh in s.shapes:
            x = emu_to_px(sh.bbox.x_emu)
            y = emu_to_px(sh.bbox.y_emu)
            w = emu_to_px(sh.bbox.w_emu)
            h = emu_to_px(sh.bbox.h_emu)
            if sh.kind.value == "text_box":
                text = " ".join(run.text for p in sh.text.paras for run in p.runs)
                out.append(f'<div class="text" style="position:absolute;left:{x}px;top:{y}px;width:{w}px;height:{h}px;overflow:hidden;">{html.escape(text)}</div>')
            elif sh.kind.value == "picture" and sh.image.media and sh.image.media.data_url:
                out.append(f'<img class="pic" src="{sh.image.media.data_url}" style="position:absolute;left:{x}px;top:{y}px;width:{w}px;height:{h}px;object-fit:contain;" />')
            elif sh.kind.value == "shape_basic":
                out.append(f'<div class="shape" style="position:absolute;left:{x}px;top:{y}px;width:{w}px;height:{h}px;border:1px solid #999;background:rgba(0,0,0,0.03)"></div>')
            elif sh.kind.value == "line":
                out.append(f'<div class="line" style="position:absolute;left:{x}px;top:{y}px;width:{w}px;height:{h}px;border-top:1px solid #666"></div>')
            elif sh.kind.value == "table":
                out.append(f'<div class="table" style="position:absolute;left:{x}px;top:{y}px;width:{w}px;height:auto;">')
                out.append('<table style="border-collapse:collapse;font-size:12px;">')
                # naive render: place cell texts row-major
                # build a simple grid
                grid = [["" for _ in range(sh.table.cols)] for _ in range(sh.table.rows)]
                for c in sh.table.cells:
                    text = " ".join(run.text for p in c.text.paras for run in p.runs)
                    grid[c.r][c.c] = html.escape(text)
                for row in grid:
                    out.append('<tr>')
                    for cell in row:
                        out.append(f'<td style="border:1px solid #ccc;padding:2px 4px;">{cell}</td>')
                    out.append('</tr>')
                out.append('</table></div>')
            elif sh.kind.value == "chart":
                out.append(f'<div class="chart" style="position:absolute;left:{x}px;top:{y}px;width:{w}px;height:{h}px;border:1px dashed #bbb;display:flex;align-items:center;justify-content:center;font:12px sans-serif;color:#666;">chart: {html.escape(sh.chart.type)}</div>')
        out.append('</div>')
        return "\n".join(out)

    def render_deck(self, docs: list[SlideDoc]) -> str:
        body = "\n".join(self.render_slide(d) for d in docs)
        return f"""
<!doctype html>
<meta charset="utf-8" />
<title>DeckDown Preview</title>
<style>
  body {{ background:#fafafa; }}
  .slide {{ box-shadow:0 2px 8px rgba(0,0,0,0.08); background:white; }}
  table td {{ min-width: 24px; }}
  img.pic {{ image-rendering:auto; }}
  .text {{ white-space:nowrap; text-overflow:ellipsis; }}
</style>
<div class="deck">
{body}
</div>
""".strip()

