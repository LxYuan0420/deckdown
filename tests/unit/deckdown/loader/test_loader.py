from __future__ import annotations

from pathlib import Path

from deckdown.loader import Loader


class TestLoader:
    @staticmethod
    def _write_min_pptx(path: Path) -> None:
        # Arrange
        from pptx import Presentation

        prs = Presentation()
        prs.save(str(path))

    def test_presentation_and_slides(self, tmp_path: Path) -> None:
        # Arrange
        pptx = tmp_path / "min.pptx"
        self._write_min_pptx(pptx)
        # Act
        loader = Loader(str(pptx))
        prs = loader.presentation()
        # Assert
        assert len(list(prs.slides)) == 0
