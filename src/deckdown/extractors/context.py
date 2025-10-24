from __future__ import annotations

from dataclasses import dataclass

from deckdown.ast import BBox, SlideSize
from deckdown.color.theme import ThemeResolver
from deckdown.media import AssetStore, MediaEmbedMode


@dataclass(frozen=True)
class ExtractContext:
    size: SlideSize
    theme: ThemeResolver
    media_mode: MediaEmbedMode = "base64"
    asset_store: AssetStore | None = None

    def bbox(self, *, left_emu: int, top_emu: int, width_emu: int, height_emu: int) -> BBox:
        width = float(self.size.width_emu or 1)
        height = float(self.size.height_emu or 1)

        def _norm(value: int, denom: float) -> float:
            # Normalized coordinates use float division with fixed 6-decimal rounding for stability.
            return round(float(value) / denom, 6)

        return BBox(
            x_emu=left_emu,
            y_emu=top_emu,
            w_emu=width_emu,
            h_emu=height_emu,
            x_norm=_norm(left_emu, width),
            y_norm=_norm(top_emu, height),
            w_norm=_norm(width_emu, width),
            h_norm=_norm(height_emu, height),
        )

    def with_offset(self, dx_emu: int, dy_emu: int) -> "ExtractContext":
        # For grouped shapes (future): an offset-aware context
        return ExtractContext(
            size=self.size,
            theme=self.theme,
            media_mode=self.media_mode,
            asset_store=self.asset_store,
        )

    def bbox_for_shape(self, shape: object) -> BBox:
        left = int(getattr(shape, "left", 0))
        top = int(getattr(shape, "top", 0))
        width = int(getattr(shape, "width", 0))
        height = int(getattr(shape, "height", 0))
        return self.bbox(left_emu=left, top_emu=top, width_emu=width, height_emu=height)
