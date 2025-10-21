from __future__ import annotations

from pathlib import Path

from deckdown.cli import EXIT_OK, main


def test_schema_writes_file(tmp_path: Path) -> None:
    out = tmp_path / "schema.json"
    code = main(["schema", "-o", str(out)])
    assert code == EXIT_OK
    text = out.read_text(encoding="utf-8")
    assert '"title": "SlideDoc"' in text or '"$defs"' in text

