from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pptx.enum.shapes import MSO_SHAPE_TYPE

from deckdown.ast import Shape, SlideDoc, SlideModel, SlideSize
from deckdown.extractors.context import ExtractContext
from deckdown.extractors.handlers.base import ShapeHandler
from deckdown.extractors.handlers.table_handler import TableShapeHandler
from deckdown.extractors.handlers.chart_handler import ChartShapeHandler
from deckdown.extractors.handlers.picture_handler import PictureShapeHandler
from deckdown.extractors.handlers.basic_line_handler import BasicShapeHandler, LineShapeHandler
from deckdown.extractors.handlers.text_handler import TextShapeHandler
from deckdown.extractors.group import GroupExtractor
from deckdown.color.theme import ThemeResolver


@dataclass(frozen=True)
class AstExtractor:
    """Build per-slide AST using focused shape handlers.

    Single path implementation (no legacy fallback). Handlers encapsulate
    per-shape logic to keep this extractor small and readable.
    """

    def extract(self, prs: Any) -> dict[int, SlideDoc]:  # noqa: ANN401
        size = SlideSize(width_emu=int(prs.slide_width), height_emu=int(prs.slide_height))
        ctx = ExtractContext(size=size, theme=ThemeResolver.from_presentation(prs))

        handlers: tuple[ShapeHandler, ...] = (
            TableShapeHandler(),
            ChartShapeHandler(),
            PictureShapeHandler(),
            LineShapeHandler(),
            BasicShapeHandler(),
            TextShapeHandler(),
        )
        group_extractor = GroupExtractor(handlers=handlers)

        out: dict[int, SlideDoc] = {}
        for idx, slide in enumerate(prs.slides, start=1):
            built: list[Shape] = []
            z = 0
            for shp in slide.shapes:
                if getattr(shp, "shape_type", None) == MSO_SHAPE_TYPE.GROUP:
                    children, z, group_shape = group_extractor.extract(shp, z_start=z, ctx=ctx)
                    built.append(group_shape)
                    built.extend(children)
                    continue
                for h in handlers:
                    if h.supports(shp):
                        shape_obj = h.build(shp, z=z, ctx=ctx)
                        if shape_obj is not None:
                            built.append(shape_obj)
                        z += 1
                        break
            out[idx] = SlideDoc(slide=SlideModel(index=idx, size=size, shapes=tuple(built)))
        return out

