from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from deckdown.ast import SlideDoc


@dataclass(frozen=True)
class MarkdownValidator:
    def find_json_blocks(self, text: str) -> list[str]:
        lines = text.splitlines()
        blocks: list[str] = []
        in_block = False
        buf: list[str] = []
        for ln in lines:
            if not in_block and ln.strip().lower() == "```json":
                in_block = True
                buf = []
                continue
            if in_block and ln.strip() == "```":
                blocks.append("\n".join(buf))
                in_block = False
                buf = []
                continue
            if in_block:
                buf.append(ln)
        return blocks

    def validate_text(self, text: str) -> list[str]:
        errors: list[str] = []
        for i, raw in enumerate(self.find_json_blocks(text), start=1):
            try:
                payload = json.loads(raw)
            except Exception as exc:  # pragma: no cover - error path exercised in tests
                errors.append(f"block {i}: invalid JSON: {exc}")
                continue
            try:
                _ = SlideDoc.model_validate(payload)
            except Exception as exc:  # pragma: no cover
                errors.append(f"block {i}: schema error: {exc}")
        return errors

    def validate_file(self, path: Path) -> list[str]:
        text = path.read_text(encoding="utf-8")
        return self.validate_text(text)

