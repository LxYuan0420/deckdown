from __future__ import annotations

import os
from dataclasses import dataclass

from deckdown.models import Deck, Slide, Table

__all__ = ["MarkdownRenderer"]


@dataclass(frozen=True)
class MarkdownRenderer:
    indent_unit: str = "  "  # two spaces per level

    def render(self, deck: Deck) -> str:
        lines: list[str] = []
        heading = self._basename(deck.file) or deck.title or "Untitled Deck"
        lines.append(f"# {heading}")
        lines.append("")

        for slide in deck.slides:
            self._render_slide(slide, lines)

        # Trim trailing blank lines and ensure a single trailing newline
        while lines and lines[-1] == "":
            lines.pop()
        return "\n".join(lines) + "\n"

    def _render_slide(self, slide: Slide, lines: list[str]) -> None:
        lines.append(f"## Slide {slide.index} — {slide.title or 'Untitled'}")
        lines.append("")

        # Text section
        text_section = self._render_text_section(slide)
        if text_section:
            lines.extend(text_section)
            lines.append("")

        # Bullets section
        bullets_section = self._render_bullets_section(slide)
        if bullets_section:
            lines.extend(bullets_section)
            lines.append("")

        # Tables section
        tables_section = self._render_tables_section(slide)
        if tables_section:
            lines.extend(tables_section)
            lines.append("")

        # Remove trailing blank line after last section, add one to separate slides
        if lines and lines[-1] == "":
            lines.pop()
        lines.append("")

    def _render_text_section(self, slide: Slide) -> list[str]:
        if not slide.text_blocks:
            return []
        out: list[str] = ["### Text"]
        for tb in slide.text_blocks:
            for para in self._sanitize_text(tb.text).split("\n"):
                out.append(para)
            out.append("")
        if out and out[-1] == "":
            out.pop()
        return out

    def _render_bullets_section(self, slide: Slide) -> list[str]:
        if not slide.bullets:
            return []
        out: list[str] = ["### Bullets"]
        for b in slide.bullets:
            indent = self.indent_unit * b.level
            text = self._one_line(self._sanitize_text(b.text))
            out.append(f"{indent}- {text}")
        return out

    def _render_tables_section(self, slide: Slide) -> list[str]:
        if not slide.tables:
            return []
        out: list[str] = ["### Tables"]
        for t in slide.tables:
            out.extend(self._render_table(t))
            out.append("")
        if out and out[-1] == "":
            out.pop()
        return out

    def _render_table(self, table: Table) -> list[str]:
        rows = [list(r) for r in table.rows]
        if not rows:
            return []

        width = max(len(r) for r in rows)
        norm: list[list[str]] = []
        for r in rows:
            clean = [self._escape_table_cell(self._one_line(self._sanitize_text(c))) for c in r]
            while len(clean) < width:
                clean.append("")
            norm.append(clean)

        out: list[str] = []
        header = "| " + " | ".join(norm[0]) + " |"
        sep = "| " + " | ".join(["---"] * width) + " |"
        out.append(header)
        out.append(sep)
        for r in norm[1:]:
            out.append("| " + " | ".join(r) + " |")
        return out

    @staticmethod
    def _sanitize_text(text: str) -> str:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        return "\n".join(part.strip() for part in text.split("\n"))

    @staticmethod
    def _one_line(text: str) -> str:
        return " ".join(text.split())

    @staticmethod
    def _escape_table_cell(text: str) -> str:
        return text.replace("|", "\\|")

    @staticmethod
    def _basename(path: str) -> str:
        base = os.path.basename(path)
        return base[:-5] if base.lower().endswith(".pptx") else base
