from __future__ import annotations

import base64
from pathlib import Path

from deckdown.cli import EXIT_OK, main

SAMPLE_PNG = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII="
)


def test_preview_generates_html(tmp_path: Path) -> None:
    md = tmp_path / "deck.md"
    md.write_text(
        '# t\n\n---\n```json\n{\n  "version": "deckdown-1",\n  "slide": {\n    "index": 1,\n    "size": {"width_emu": 9144000, "height_emu": 5143500},\n    "shapes": [\n      {\n        "id": "s1",\n        "kind": "text_box",\n        "bbox": {"x_emu": 914400, "y_emu": 914400, "w_emu": 1828800, "h_emu": 914400, "x_norm": 0.1, "y_norm": 0.1, "w_norm": 0.2, "h_norm": 0.178},\n        "z": 0,\n        "text": { "paras": [ { "lvl": 0, "runs": [ { "text": "Hello" } ] } ] }\n      }\n    ]\n  }\n}\n```\n',
        encoding="utf-8",
    )
    out = tmp_path / "preview.html"
    code = main(["preview", str(md), "-o", str(out)])
    assert code == EXIT_OK
    html = out.read_text(encoding="utf-8")
    assert "<!doctype html>" in html and 'class="slide"' in html


def test_preview_inlines_referenced_picture(tmp_path: Path) -> None:
    assets_dir = tmp_path / "deck_assets"
    assets_dir.mkdir()
    image_path = assets_dir / "img-001.png"
    image_path.write_bytes(base64.b64decode(SAMPLE_PNG))

    md = tmp_path / "deck.md"
    md.write_text(
        '# t\n\n---\n```json\n{\n  "version": "deckdown-1",\n  "slide": {\n    "index": 1,\n    "size": {"width_emu": 9144000, "height_emu": 5143500},\n    "shapes": [\n      {\n        "id": "s1",\n        "kind": "picture",\n        "bbox": {"x_emu": 914400, "y_emu": 914400, "w_emu": 1828800, "h_emu": 914400, "x_norm": 0.1, "y_norm": 0.1, "w_norm": 0.2, "h_norm": 0.178},\n        "z": 0,\n        "image": { "media": { "ref": "deck_assets/img-001.png" } }\n      }\n    ]\n  }\n}\n```\n',
        encoding="utf-8",
    )
    out = tmp_path / "preview.html"
    code = main(["preview", str(md), "-o", str(out)])
    assert code == EXIT_OK
    html = out.read_text(encoding="utf-8")
    assert "data:image/png;base64" in html
