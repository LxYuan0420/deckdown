from __future__ import annotations

from dataclasses import dataclass

from deckdown.ast import BBox, SlideSize


@dataclass(frozen=True)
class ExtractContext:
    size: SlideSize

    def bbox(self, *, left_emu: int, top_emu: int, width_emu: int, height_emu: int) -> BBox:
        w = self.size.width_emu or 1
        h = self.size.height_emu or 1
        return BBox(
            x_emu=left_emu,
            y_emu=top_emu,
            w_emu=width_emu,
            h_emu=height_emu,
            x_norm=round(left_emu / w, 6),
            y_norm=round(top_emu / h, 6),
            w_norm=round(width_emu / w, 6),
            h_norm=round(height_emu / h, 6),
        )

