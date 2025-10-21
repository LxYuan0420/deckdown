from __future__ import annotations

from pathlib import Path

from deckdown.cli import EXIT_OK, main


def test_validate_ok(tmp_path: Path) -> None:
    # Arrange
    md = tmp_path / "deck.md"
    md.write_text(
        "# t\n\n---\n```json\n{\n  \"version\": \"deckdown-1\",\n  \"slide\": {\n    \"index\": 1,\n    \"size\": {\"width_emu\": 1, \"height_emu\": 1},\n    \"shapes\": []\n  }\n}\n```\n",
        encoding="utf-8",
    )
    # Act
    code = main(["validate", str(md)])
    # Assert
    assert code == EXIT_OK

