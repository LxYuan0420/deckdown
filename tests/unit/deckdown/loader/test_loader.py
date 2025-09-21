from __future__ import annotations

from pathlib import Path

from deckdown.loader import Loader


def _write_min_pptx(path: Path) -> None:
    from pptx import Presentation

    prs = Presentation()
    prs.save(str(path))


def test_loader_presentation_and_slides(tmp_path: Path) -> None:
    pptx = tmp_path / "min.pptx"
    _write_min_pptx(pptx)

    loader = Loader(str(pptx))
    prs = loader.presentation()
    assert len(list(prs.slides)) == 0
