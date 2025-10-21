from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Any

from pptx.enum.shapes import MSO_SHAPE_TYPE

from deckdown.ast import (
    BBox,
    Media,
    Paragraph,
    PicturePayload,
    PictureShape,
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

                # text shapes
                if getattr(shp, "has_text_frame", False):
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
                        payload = PicturePayload(media=Media(data_url=data_url))
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

                # Other kinds (tables, charts, groups) will arrive in later milestones

            slide_model = SlideModel(index=idx, size=size, shapes=tuple(shapes))
            out[idx] = SlideDoc(slide=slide_model)
        return out

