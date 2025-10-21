from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from pptx import Presentation
from pptx.util import Emu

from deckdown.ast import ChartShape, LineShape, PictureShape, SlideDoc, TableShape, TextShape, BasicShape


@dataclass(frozen=True)
class DeckAssembler:
    def assemble(self, docs: Iterable[SlideDoc], *, out: Path) -> None:
        prs = Presentation()
        blank = prs.slide_layouts[6]
        # Ensure empty deck
        while len(prs.slides) > 0:
            rId = prs.slides._sldIdLst[0].rId  # type: ignore[attr-defined]
            prs.part.drop_rel(rId)
            prs.slides._sldIdLst.remove(prs.slides._sldIdLst[0])  # type: ignore[attr-defined]

        for doc in docs:
            s = prs.slides.add_slide(blank)
            # Optionally, set slide size if needed (global, not per-slide in PPTX)
            # Place basic text and pictures to validate pipeline
            for sh in doc.slide.shapes:
                if isinstance(sh, TextShape):
                    # naive: add a textbox at bbox and write plain text by concatenating runs
                    left = Emu(sh.bbox.x_emu); top = Emu(sh.bbox.y_emu); width = Emu(sh.bbox.w_emu); height = Emu(sh.bbox.h_emu)
                    tx = s.shapes.add_textbox(left, top, width, height)
                    tf = tx.text_frame
                    tf.clear()
                    first = True
                    for p in sh.text.paras:
                        if first:
                            par = tf.paragraphs[0]
                            first = False
                        else:
                            par = tf.add_paragraph()
                        par.level = p.lvl
                        par.text = "".join(r.text for r in p.runs)
                elif isinstance(sh, PictureShape) and sh.image.media.data_url:
                    # simple approach: skip decoding; future: decode data_url -> image stream
                    pass
                # Tables/Charts/Basic/Line handling deferred to later milestones

        prs.save(str(out))

