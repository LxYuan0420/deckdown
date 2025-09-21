from __future__ import annotations

from pathlib import Path

from deckdown.cli import EXIT_INPUT_ERROR, EXIT_OK, main


def _write_min_pptx(path: Path) -> None:
    # Create a minimal valid PPTX (no slides)
    from pptx import Presentation

    prs = Presentation()
    prs.save(str(path))


def test_cli_extract_writes_markdown(tmp_path: Path) -> None:
    pptx = tmp_path / "sample.pptx"
    _write_min_pptx(pptx)
    out = tmp_path / "out.md"

    code = main(["extract", str(pptx), "--md-out", str(out)])
    assert code == EXIT_OK
    text = out.read_text(encoding="utf-8")
    assert text.startswith("# sample\n")


def test_cli_extract_default_output_name(tmp_path: Path) -> None:
    pptx = tmp_path / "Deck Name.PPTX"  # ensure case-insensitivity
    _write_min_pptx(pptx)

    code = main(["extract", str(pptx)])
    assert code == EXIT_OK
    out = tmp_path / "Deck Name.md"
    assert out.exists()


def test_cli_missing_input_returns_error(tmp_path: Path) -> None:
    missing = tmp_path / "missing.pptx"
    code = main(["extract", str(missing)])
    assert code == EXIT_INPUT_ERROR


def test_cli_input_directory_is_error(tmp_path: Path) -> None:
    code = main(["extract", str(tmp_path)])
    assert code == EXIT_INPUT_ERROR


def test_cli_md_out_directory(tmp_path: Path) -> None:
    pptx = tmp_path / "deck.pptx"
    _write_min_pptx(pptx)
    outdir = tmp_path / "out"
    code = main(["extract", str(pptx), "--md-out", str(outdir)])
    assert code == EXIT_OK
    expected = outdir / "deck.md"
    assert expected.exists()
