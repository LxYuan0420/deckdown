from __future__ import annotations

from pathlib import Path

from deckdown.cli import EXIT_INPUT_ERROR, EXIT_OK, main


class TestCLIExtract:
    @staticmethod
    def _write_min_pptx(path: Path) -> None:
        # Arrange: create a minimal valid PPTX (no slides)
        from pptx import Presentation

        prs = Presentation()
        prs.save(str(path))

    def test_writes_markdown(self, tmp_path: Path) -> None:
        # Arrange
        pptx = tmp_path / "sample.pptx"
        self._write_min_pptx(pptx)
        out = tmp_path / "out.md"
        # Act
        code = main(["extract", str(pptx), "--md-out", str(out)])
        # Assert
        assert code == EXIT_OK
        text = out.read_text(encoding="utf-8")
        assert text.startswith("# sample\n")

    def test_default_output_name(self, tmp_path: Path) -> None:
        # Arrange
        pptx = tmp_path / "Deck Name.PPTX"  # ensure case-insensitivity
        self._write_min_pptx(pptx)
        # Act
        code = main(["extract", str(pptx)])
        # Assert
        assert code == EXIT_OK
        out = tmp_path / "Deck Name.md"
        assert out.exists()

    def test_missing_input_returns_error(self, tmp_path: Path) -> None:
        # Arrange
        missing = tmp_path / "missing.pptx"
        # Act
        code = main(["extract", str(missing)])
        # Assert
        assert code == EXIT_INPUT_ERROR

    def test_input_directory_is_error(self, tmp_path: Path) -> None:
        # Arrange & Act
        code = main(["extract", str(tmp_path)])
        # Assert
        assert code == EXIT_INPUT_ERROR

    def test_md_out_directory(self, tmp_path: Path) -> None:
        # Arrange
        pptx = tmp_path / "deck.pptx"
        self._write_min_pptx(pptx)
        outdir = tmp_path / "out"
        # Act
        code = main(["extract", str(pptx), "--md-out", str(outdir)])
        # Assert
        assert code == EXIT_OK
        expected = outdir / "deck.md"
        assert expected.exists()
