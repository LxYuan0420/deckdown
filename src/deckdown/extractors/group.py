from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from pptx.enum.shapes import MSO_SHAPE_TYPE

from deckdown.ast import GroupShape, Shape
from deckdown.extractors.context import ExtractContext
from deckdown.extractors.handlers.base import ShapeHandler


@dataclass(frozen=True)
class GroupExtractor:
    handlers: tuple[ShapeHandler, ...]

    def extract(self, grp: Any, *, z_start: int, ctx: ExtractContext) -> tuple[list[Shape], int, GroupShape]:  # noqa: ANN401
        z = z_start
        out: list[Shape] = []
        child_ids: list[str] = []
        group_id = f"g{getattr(grp, 'shape_id', z_start)}"
        # Parent group bbox in absolute coordinates
        bbox = ctx.bbox(
            left_emu=int(getattr(grp, "left", 0)),
            top_emu=int(getattr(grp, "top", 0)),
            width_emu=int(getattr(grp, "width", 0)),
            height_emu=int(getattr(grp, "height", 0)),
        )
        # Child coordinates are relative to group origin; create an offset-aware context if needed.
        # Current ctx.bbox returns absolute since we pass absolute values: left+child.left, etc.
        # We'll compute absolute by adding group offsets ourselves when building children.
        gx, gy = int(getattr(grp, "left", 0)), int(getattr(grp, "top", 0))

        for shp in grp.shapes:
            # Compute absolute bbox by temporarily patching left/top for child object through getters
            # Simpler: most handlers compute bbox via shape.left/top; we can create a small proxy with adjusted left/top
            proxy = _ShapeProxy(shp, dx=gx, dy=gy)
            built = None
            for h in self.handlers:
                if h.supports(proxy):
                    built = h.build(proxy, z=z, ctx=ctx)
                    break
            if built is not None:
                # tag with group id using model_copy since models are frozen
                built = built.model_copy(update={"group": group_id})  # type: ignore[attr-defined]
                out.append(built)
                child_ids.append(built.id)
                z += 1

        group_shape = GroupShape(
            id=group_id,
            kind="group",
            name=getattr(grp, "name", None),
            bbox=bbox,
            z=z_start,  # container z at start; children z continue afterwards
            rotation=None,
            children=tuple(child_ids),
        )
        return out, z, group_shape


class _ShapeProxy:
    def __init__(self, shp: Any, *, dx: int, dy: int) -> None:  # noqa: ANN401
        self._shp = shp
        self._dx = dx
        self._dy = dy

    def __getattr__(self, name: str):  # noqa: D401
        if name == "left":
            return int(getattr(self._shp, "left", 0)) + self._dx
        if name == "top":
            return int(getattr(self._shp, "top", 0)) + self._dy
        return getattr(self._shp, name)

