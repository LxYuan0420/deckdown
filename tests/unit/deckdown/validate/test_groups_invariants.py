from __future__ import annotations

from pathlib import Path

from deckdown.cli import EXIT_OK, main


def test_validate_group_invariants(tmp_path: Path) -> None:
    md = tmp_path / "deck.md"
    # group references missing child and child has wrong backlink
    md.write_text(
        "# t\n\n---\n```json\n{\n  \"version\": \"deckdown-1\",\n  \"slide\": {\n    \"index\": 1,\n    \"size\": {\"width_emu\": 9144000, \"height_emu\": 5143500},\n    \"shapes\": [\n      { \"id\": \"g1\", \"kind\": \"group\", \"bbox\": {\"x_emu\":0,\"y_emu\":0,\"w_emu\":0,\"h_emu\":0,\"x_norm\":0,\"y_norm\":0,\"w_norm\":0,\"h_norm\":0}, \"z\": 0, \"children\": [\"s-missing\"] },\n      { \"id\": \"s2\", \"kind\": \"text_box\", \"bbox\": {\"x_emu\":0,\"y_emu\":0,\"w_emu\":0,\"h_emu\":0,\"x_norm\":0,\"y_norm\":0,\"w_norm\":0,\"h_norm\":0}, \"z\": 1, \"text\": {\"paras\":[{\"lvl\":0,\"runs\":[{\"text\":\"A\"}]}]}, \"group\": \"g2\" }\n    ]\n  }\n}\n```\n",
        encoding="utf-8",
    )
    code = main(["validate", str(md)])
    assert code != EXIT_OK

