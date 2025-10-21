from __future__ import annotations

from pathlib import Path

from deckdown.cli import EXIT_OK, main


def test_assemble_sets_slide_size(tmp_path: Path) -> None:
    md = tmp_path / "deck.md"
    # 10x6 inches in EMU
    w_emu, h_emu = 9144000, 5486400
    md.write_text(
        f"# t\n\n---\n```json\n{{\n  \"version\": \"deckdown-1\",\n  \"slide\": {{\n    \"index\": 1,\n    \"size\": {{\"width_emu\": {w_emu}, \"height_emu\": {h_emu}}},\n    \"shapes\": []\n  }}\n}}\n```\n",
        encoding="utf-8",
    )
    out = tmp_path / "out.pptx"
    code = main(["assemble", str(md), "-o", str(out)])
    assert code == EXIT_OK

    from pptx import Presentation
    from pptx.util import Emu

    prs = Presentation(str(out))
    assert int(prs.slide_width) == w_emu
    assert int(prs.slide_height) == h_emu

