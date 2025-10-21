from __future__ import annotations

from typing import Any

from deckdown.ast import Paragraph, TextPayload, TextRun
from deckdown.color.theme import ThemeResolver


def align_to_str(align: Any) -> str | None:  # noqa: ANN401
    try:
        name = align._member_name_  # type: ignore[attr-defined]
    except Exception:
        return None
    low = name.lower()
    return low if low in {"left", "center", "right", "justify"} else None


def color_dict_from_font(font: Any, theme: ThemeResolver) -> dict | None:  # noqa: ANN401
    try:
        col = getattr(font, "color", None)
        if col is None:
            return None
        data = theme.color_dict_from_colorformat(col)
        if data:
            return data
    except Exception:
        return None
    return None


def extract_text_payload(text_frame: Any, theme: ThemeResolver) -> TextPayload:  # noqa: ANN401
    paras: list[Paragraph] = []
    try:
        for p in text_frame.paragraphs:
            runs: list[TextRun] = []
            for r in p.runs:
                font = {}
                f = r.font
                if f is not None and f.size is not None:
                    try:
                        font["size_pt"] = round(float(f.size.pt), 2)  # type: ignore[union-attr]
                    except Exception:
                        pass
                if f is not None and f.name:
                    font["family"] = f.name
                if f is not None and f.bold is not None:
                    font["bold"] = bool(f.bold)
                if f is not None and f.italic is not None:
                    font["italic"] = bool(f.italic)
                if f is not None and f.underline is not None:
                    font["underline"] = bool(f.underline)
                c = color_dict_from_font(f, theme)
                if c:
                    font["color"] = c
                runs.append(TextRun(text=r.text or "", font=font or None))
            paras.append(
                Paragraph(
                    lvl=int(getattr(p, "level", 0) or 0),
                    align=align_to_str(getattr(p, "alignment", None)),
                    runs=tuple(runs),
                )
            )
    except Exception:  # pragma: no cover
        pass
    return TextPayload(paras=tuple(paras))
