from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

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
                doc = SlideDoc.model_validate(payload)
            except Exception as exc:  # pragma: no cover
                errors.append(f"block {i}: schema error: {exc}")
                continue
            # invariants
            errs = self._check_invariants(doc)
            for e in errs:
                errors.append(f"block {i}: {e}")
        return errors

    def validate_file(self, path: Path) -> list[str]:
        text = path.read_text(encoding="utf-8")
        return self.validate_text(text)

    def _check_invariants(self, doc: SlideDoc) -> list[str]:
        errs: list[str] = []
        slide = doc.slide
        errs.extend(self._check_ids_and_bbox(slide))
        errs.extend(self._check_chart_lengths(slide))
        errs.extend(self._check_groups(slide))
        return errs

    def _check_ids_and_bbox(self, slide) -> list[str]:  # noqa: ANN401
        errs: list[str] = []
        w = slide.size.width_emu or 1
        h = slide.size.height_emu or 1
        seen_ids: set[str] = set()
        last_z = -1
        for sh in slide.shapes:
            if sh.id in seen_ids:
                errs.append(f"duplicate shape id: {sh.id}")
            else:
                seen_ids.add(sh.id)
            if hasattr(sh, "z") and sh.z < last_z:
                errs.append("z-order is not non-decreasing")
            if hasattr(sh, "z"):
                last_z = sh.z
            bb = sh.bbox
            if bb.w_emu < 0 or bb.h_emu < 0:
                errs.append(f"negative size for shape {sh.id}")
            if bb.x_emu < 0 or bb.y_emu < 0 or bb.x_emu + bb.w_emu > w or bb.y_emu + bb.h_emu > h:
                errs.append(f"shape {sh.id} bbox out of slide bounds")
        return errs

    def _check_chart_lengths(self, slide) -> list[str]:  # noqa: ANN401
        errs: list[str] = []
        for sh in slide.shapes:
            if hasattr(sh, "kind") and sh.kind.value == "chart":
                cats = tuple(getattr(sh.chart, "categories", ()) or ())
                for ser in sh.chart.series or ():
                    if len(ser.values or ()) != len(cats):
                        errs.append(f"chart series length != categories for shape {sh.id}")
        return errs

    def _check_groups(self, slide) -> list[str]:  # noqa: ANN401
        errs: list[str] = []
        id_to_shape = {sh.id: sh for sh in slide.shapes}
        for sh in slide.shapes:
            if hasattr(sh, "kind") and sh.kind.value == "group":
                for cid in getattr(sh, "children", ()):  # type: ignore[attr-defined]
                    if cid not in id_to_shape:
                        errs.append(f"group {sh.id} references missing child id {cid}")
                    else:
                        child = id_to_shape[cid]
                        if getattr(child, "group", None) != sh.id:
                            errs.append(f"child {cid} missing group backlink to {sh.id}")
        group_ids = {sh.id for sh in slide.shapes if hasattr(sh, "kind") and sh.kind.value == "group"}
        for sh in slide.shapes:
            g = getattr(sh, "group", None)
            if g and g not in group_ids:
                errs.append(f"shape {sh.id} has non-existent group id {g}")
        return errs
