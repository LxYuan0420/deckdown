from __future__ import annotations

from pathlib import Path

from deckdown.io import OutputManager


class TestOutputManager:
    def test_default_path_uses_basename(self, tmp_path: Path) -> None:
        # Arrange
        om = OutputManager()
        p = tmp_path / "Deck Name.PPTX"
        p.write_bytes(b"\x50\x4b")
        # Act
        out = om.derive_markdown_path_next_to_input(p)
        # Assert
        assert out.name == "Deck Name.md"

    def test_resolve_to_directory_existing(self, tmp_path: Path) -> None:
        # Arrange
        om = OutputManager()
        input_p = tmp_path / "x.pptx"
        input_p.write_bytes(b"")
        outdir = tmp_path / "out"
        outdir.mkdir()
        # Act
        result = om.resolve_markdown_output_path(input_p, outdir)
        # Assert
        assert result == outdir / "x.md"

    def test_resolve_trailing_slash(self, tmp_path: Path) -> None:
        # Arrange
        om = OutputManager()
        input_p = tmp_path / "y.pptx"
        input_p.write_bytes(b"")
        # Act
        result = om.resolve_markdown_output_path(input_p, str(tmp_path / "folder") + "/")
        # Assert
        assert result == (tmp_path / "folder" / "y.md")

    def test_resolve_nonexistent_no_ext_means_dir(self, tmp_path: Path) -> None:
        # Arrange
        om = OutputManager()
        input_p = tmp_path / "z.pptx"
        input_p.write_bytes(b"")
        dest = tmp_path / "dest_dir"
        # Act
        result = om.resolve_markdown_output_path(input_p, dest)
        # Assert
        assert result == dest / "z.md"

    def test_resolve_explicit_file(self, tmp_path: Path) -> None:
        # Arrange
        om = OutputManager()
        input_p = tmp_path / "a.pptx"
        input_p.write_bytes(b"")
        dest = tmp_path / "explicit.md"
        # Act
        result = om.resolve_markdown_output_path(input_p, dest)
        # Assert
        assert result == dest

    def test_write_text_file_creates_parents(self, tmp_path: Path) -> None:
        # Arrange
        om = OutputManager()
        dest = tmp_path / "nested" / "file.md"
        # Act
        om.write_text_file(dest, "hello")
        # Assert
        assert dest.exists()
        assert dest.read_text(encoding="utf-8") == "hello"
