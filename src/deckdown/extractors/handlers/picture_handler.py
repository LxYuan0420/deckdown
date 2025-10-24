from __future__ import annotations

import base64
from typing import Any, Optional

from pptx.enum.shapes import MSO_SHAPE_TYPE

from deckdown.ast import CropSpec, Media, PicturePayload, PictureShape, ShapeKind
from deckdown.extractors.context import ExtractContext
from deckdown.extractors.handlers.base import ShapeHandler


class PictureShapeHandler(ShapeHandler):
    def supports(self, shape: Any) -> bool:  # noqa: ANN401
        return getattr(shape, "shape_type", None) == MSO_SHAPE_TYPE.PICTURE

    def build(self, shape: Any, *, z: int, ctx: ExtractContext) -> Optional[PictureShape]:  # noqa: ANN401
        bbox = ctx.bbox_for_shape(shape)
        blob: bytes | None = None
        content_type = "application/octet-stream"
        try:
            image = getattr(shape, "image", None)
            if image is not None:
                blob = getattr(image, "blob", None)
                content_type = getattr(image, "content_type", content_type)
        except Exception:
            blob = None
            content_type = "application/octet-stream"

        data_url: str | None = None
        try:
            include_data_url = ctx.media_mode == "base64" or ctx.asset_store is None
            if blob and include_data_url:
                b64 = base64.b64encode(blob).decode("ascii")
                data_url = f"data:{content_type};base64,{b64}"
        except Exception:
            data_url = None

        ref: str | None = None
        if blob and ctx.media_mode == "refs" and ctx.asset_store is not None:
            hint_raw = getattr(shape, "name", None)
            hint = str(hint_raw) if hint_raw else None
            ref = ctx.asset_store.save_image(
                blob=blob,
                content_type=content_type,
                name_hint=hint,
            )

        # crop values
        crop: CropSpec | None = None
        try:
            cl = float(getattr(shape, "crop_left", 0.0) or 0.0)
            cr = float(getattr(shape, "crop_right", 0.0) or 0.0)
            ct = float(getattr(shape, "crop_top", 0.0) or 0.0)
            cb = float(getattr(shape, "crop_bottom", 0.0) or 0.0)
            if any(v != 0.0 for v in (cl, cr, ct, cb)):
                crop = CropSpec(left=cl, right=cr, top=ct, bottom=cb)
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
        payload = PicturePayload(
            media=Media(data_url=data_url, ref=ref),
            crop=crop,
            opacity=None,
            alt=alt,
        )
        return PictureShape(
            id=f"s{getattr(shape, 'shape_id', z)}",
            kind=ShapeKind.PICTURE,
            name=getattr(shape, "name", None),
            bbox=bbox,
            z=z,
            rotation=rot,
            image=payload,
        )
