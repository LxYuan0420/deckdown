from __future__ import annotations

from pathlib import Path

from deckdown.io import OutputManager


def test_default_path_uses_basename(tmp_path: Path) -> None:
    om = OutputManager()
    p = tmp_path / "Deck Name.PPTX"
    p.write_bytes(b"\x50\x4b")  # minimal zip header not required, just to create file
    out = om.derive_markdown_path_next_to_input(p)
    assert out.name == "Deck Name.md"


def test_resolve_to_directory_existing(tmp_path: Path) -> None:
    om = OutputManager()
    input_p = tmp_path / "x.pptx"
    input_p.write_bytes(b"")
    outdir = tmp_path / "out"
    outdir.mkdir()
    result = om.resolve_markdown_output_path(input_p, str(outdir))
    assert result == outdir / "x.md"


def test_resolve_trailing_slash(tmp_path: Path) -> None:
    om = OutputManager()
    input_p = tmp_path / "y.pptx"
    input_p.write_bytes(b"")
    result = om.resolve_markdown_output_path(input_p, str(tmp_path / "folder") + "/")
    assert result == (tmp_path / "folder" / "y.md")


def test_resolve_nonexistent_no_ext_means_dir(tmp_path: Path) -> None:
    om = OutputManager()
    input_p = tmp_path / "z.pptx"
    input_p.write_bytes(b"")
    dest = tmp_path / "dest_dir"
    result = om.resolve_markdown_output_path(input_p, str(dest))
    assert result == dest / "z.md"


def test_resolve_explicit_file(tmp_path: Path) -> None:
    om = OutputManager()
    input_p = tmp_path / "a.pptx"
    input_p.write_bytes(b"")
    dest = tmp_path / "explicit.md"
    result = om.resolve_markdown_output_path(input_p, str(dest))
    assert result == dest


def test_write_text_file_creates_parents(tmp_path: Path) -> None:
    om = OutputManager()
    dest = tmp_path / "nested" / "file.md"
    om.write_text_file(dest, "hello")
    assert dest.exists()
    assert dest.read_text(encoding="utf-8") == "hello"

