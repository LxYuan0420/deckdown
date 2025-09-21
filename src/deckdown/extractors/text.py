from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from collections.abc import Iterable

from deckdown.models import Bullet, Deck, Slide, TextBlock


@dataclass(frozen=True)
class ParagraphSplitter:
    def split(self, paragraphs: list[tuple[str, int]]) -> tuple[list[str], list[Bullet]]:
        first_bullet = next((i for i, (_, lvl) in enumerate(paragraphs) if lvl > 0), None)
        if first_bullet is None:
            return [t for t, _ in paragraphs], []
        start = max(first_bullet - 1, 0)
        body = [t for t, _ in paragraphs[:start]] if start > 0 else []
        items = [Bullet(level=lvl, text=t) for t, lvl in paragraphs[start:]]
        return body, items


@dataclass(frozen=True)
class ShapeOrderer:
    def text_shapes(self, slide: Any) -> Iterable[Any]:  # noqa: ANN401
        shapes = [s for s in slide.shapes if getattr(s, "has_text_frame", False)]
        shapes.sort(key=lambda s: (int(getattr(s, "top", 0)), int(getattr(s, "left", 0))))
        return shapes


@dataclass(frozen=True)
class SlideTextExtractor:
    orderer: ShapeOrderer
    splitter: ParagraphSplitter

    def extract(self, index: int, slide: Any) -> Slide:  # noqa: ANN401
        title = self._extract_title(slide)
        blocks: list[TextBlock] = []
        bullets: list[Bullet] = []
        title_shape = getattr(slide.shapes, "title", None)
        for shape in self.orderer.text_shapes(slide):
            if title_shape is not None and shape is title_shape:
                continue
            paragraphs = self._collect_paragraphs(shape)
            if not paragraphs:
                continue
            if title and len(paragraphs) == 1 and paragraphs[0][0] == title:
                continue
            body_lines, bullet_items = self.splitter.split(paragraphs)
            if body_lines:
                blocks.append(TextBlock(text="\n".join(body_lines)))
            bullets.extend(bullet_items)
        return Slide(
            index=index,
            title=title,
            text_blocks=tuple(blocks),
            bullets=tuple(bullets),
            tables=(),
            charts=(),
        )

    def _extract_title(self, slide: Any) -> str | None:  # noqa: ANN401
        try:
            title_shape = slide.shapes.title
        except Exception:
            title_shape = None
        if title_shape is None or not getattr(title_shape, "has_text_frame", False):
            return None
        text = getattr(title_shape.text_frame.paragraphs[0], "text", "")
        t = (text or "").strip()
        return t or None

    def _collect_paragraphs(self, shape: Any) -> list[tuple[str, int]]:  # noqa: ANN401
        frame = shape.text_frame
        out: list[tuple[str, int]] = []
        for p in frame.paragraphs:
            txt = (p.text or "").strip()
            if not txt:
                continue
            lvl = int(getattr(p, "level", 0) or 0)
            out.append((txt, lvl))
        return out


@dataclass(frozen=True)
class TextExtractor:
    with_notes: bool = False
    orderer: ShapeOrderer = ShapeOrderer()
    splitter: ParagraphSplitter = ParagraphSplitter()

    def extract_deck(self, prs: Any, *, source_path: str) -> Deck:  # noqa: ANN401
        slide_extractor = SlideTextExtractor(self.orderer, self.splitter)
        slides = [slide_extractor.extract(i, s) for i, s in enumerate(prs.slides, start=1)]
        title = self._derive_deck_title(prs, slide_extractor)
        return Deck(file=source_path, title=title, slides=tuple(slides))

    def _derive_deck_title(self, prs: Any, slide_extractor: SlideTextExtractor) -> str | None:  # noqa: ANN401
        try:
            first = next(iter(prs.slides))
        except StopIteration:
            first = None
        if first is not None:
            t = slide_extractor._extract_title(first)
            if t:
                return t
        try:
            title = prs.core_properties.title
            if title:
                return str(title)
        except Exception:
            return None
        return None
