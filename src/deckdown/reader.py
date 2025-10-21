from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Iterable

from deckdown.ast import SlideDoc


@dataclass(frozen=True)
class MarkdownReader:
    def iter_blocks(self, text: str) -> Iterable[str]:
        lines = text.splitlines()
        in_block = False
        buf: list[str] = []
        for ln in lines:
            if not in_block and ln.strip().lower() == "```json":
                in_block = True
                buf = []
                continue
            if in_block and ln.strip() == "```":
                yield "\n".join(buf)
                in_block = False
                buf = []
                continue
            if in_block:
                buf.append(ln)

    def load_file(self, path: Path) -> list[SlideDoc]:
        text = path.read_text(encoding="utf-8")
        docs: list[SlideDoc] = []
        for raw in self.iter_blocks(text):
            payload = json.loads(raw)
            docs.append(SlideDoc.model_validate(payload))
        return docs
