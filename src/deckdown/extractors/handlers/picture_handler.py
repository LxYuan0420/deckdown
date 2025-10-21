from __future__ import annotations

import base64
from typing import Any, Optional

from pptx.enum.shapes import MSO_SHAPE_TYPE

from deckdown.ast import Media, PicturePayload, PictureShape, ShapeKind
from deckdown.extractors.context import ExtractContext
from deckdown.extractors.handlers.base import ShapeHandler


class PictureShapeHandler(ShapeHandler):
    def supports(self, shape: Any) -> bool:  # noqa: ANN401
        return getattr(shape, "shape_type", None) == MSO_SHAPE_TYPE.PICTURE

    def build(self, shape: Any, *, z: int, ctx: ExtractContext) -> Optional[PictureShape]:  # noqa: ANN401
        bbox = ctx.bbox(
            left_emu=int(getattr(shape, "left", 0)),
            top_emu=int(getattr(shape, "top", 0)),
            width_emu=int(getattr(shape, "width", 0)),
            height_emu=int(getattr(shape, "height", 0)),
        )
        # data URL
        data_url = None
        try:
            blob = getattr(shape.image, "blob", None)
            ct = getattr(shape.image, "content_type", "application/octet-stream")
            if blob:
                b64 = base64.b64encode(blob).decode("ascii")
                data_url = f"data:{ct};base64,{b64}"
        except Exception:
            data_url = None
        # crop values
        crop = None
        try:
            cl = float(getattr(shape, "crop_left", 0.0) or 0.0)
            cr = float(getattr(shape, "crop_right", 0.0) or 0.0)
            ct = float(getattr(shape, "crop_top", 0.0) or 0.0)
            cb = float(getattr(shape, "crop_bottom", 0.0) or 0.0)
            if any(v != 0.0 for v in (cl, cr, ct, cb)):
                crop = {"left": cl, "right": cr, "top": ct, "bottom": cb}
        except Exception:
            crop = None
        alt = None
        try:
            alt = getattr(shape, "alternative_text", None)
            if alt:
                alt = str(alt)
        except Exception:
            alt = None
        rot = None
        try:
            rot = float(getattr(shape, "rotation"))  # type: ignore[arg-type]
        except Exception:
            rot = None
        payload = PicturePayload(media=Media(data_url=data_url), crop=crop, opacity=None, alt=alt)
        return PictureShape(
            id=f"s{getattr(shape, 'shape_id', z)}",
            kind=ShapeKind.PICTURE,
            name=getattr(shape, "name", None),
            bbox=bbox,
            z=z,
            rotation=rot,
            image=payload,
        )

