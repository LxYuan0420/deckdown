from __future__ import annotations

from pathlib import Path

from deckdown.cli import EXIT_OK, main


def test_assemble_minimal(tmp_path: Path) -> None:
    md = tmp_path / "deck.md"
    md.write_text(
        "# t\n\n---\n```json\n{\n  \"version\": \"deckdown-1\",\n  \"slide\": {\n    \"index\": 1,\n    \"size\": {\"width_emu\": 9144000, \"height_emu\": 5143500},\n    \"shapes\": [\n      {\n        \"id\": \"s1\",\n        \"kind\": \"text_box\",\n        \"bbox\": {\"x_emu\": 914400, \"y_emu\": 914400, \"w_emu\": 1828800, \"h_emu\": 914400, \"x_norm\": 0.1, \"y_norm\": 0.1, \"w_norm\": 0.2, \"h_norm\": 0.178},\n        \"z\": 0,\n        \"text\": {\n          \"paras\": [ { \"lvl\": 0, \"runs\": [ { \"text\": \"Hello\" } ] } ]\n        }\n      }\n    ]\n  }\n}\n```\n",
        encoding="utf-8",
    )
    out = tmp_path / "out.pptx"
    code = main(["assemble", str(md), "-o", str(out)])
    assert code == EXIT_OK
    assert out.exists() and out.stat().st_size > 0

