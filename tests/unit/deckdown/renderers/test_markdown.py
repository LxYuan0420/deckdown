from __future__ import annotations

from deckdown.models import Bullet, Deck, Slide, Table, TextBlock
from deckdown.renderers.markdown import MarkdownRenderer


def test_render_markdown_basic() -> None:
    tb = TextBlock(text="Alpha\nBeta")
    bullets = (
        Bullet(level=0, text="Item 1"),
        Bullet(level=1, text="Sub 1"),
    )
    table = Table(
        rows=(
            ("H1", "H2"),
            ("A|A", "B\nB"),
        )
    )
    slide = Slide(index=1, title="Intro", text_blocks=(tb,), bullets=bullets, tables=(table,))
    deck = Deck(file="sample.pptx", title="Sample", slides=(slide,))

    md = MarkdownRenderer().render(deck)
    expected = (
        "# sample\n\n"
        "## Slide 1 — Intro\n\n"
        "### Text\n"
        "Alpha\n"
        "Beta\n\n"
        "### Bullets\n"
        "- Item 1\n"
        "  - Sub 1\n\n"
        "### Tables\n"
        "| H1 | H2 |\n"
        "| --- | --- |\n"
        "| A\\|A | B B |\n"
    )
    assert md == expected


def test_markdown_renderer_class() -> None:
    # Same as above but exercise the OOFP class directly
    slide = Slide(index=1, title="Intro", text_blocks=(TextBlock(text="A"),), bullets=(), tables=())
    deck = Deck(file="sample.pptx", title="Sample", slides=(slide,))
    renderer = MarkdownRenderer()
    out = renderer.render(deck)
    assert out.startswith("# sample\n\n## Slide 1 — Intro\n")


def test_renderer_tables_empty_and_ragged_and_title_fallback() -> None:
    # Empty table should render only the section header (no rows)
    slide1 = Slide(index=1, title=None, text_blocks=(), bullets=(), tables=(Table(rows=()),))
    # Ragged table second row shorter than header
    table = Table(
        rows=(
            ("H1", "H2", "H3"),
            ("A",),
        )
    )
    slide2 = Slide(index=2, title="T", text_blocks=(), bullets=(), tables=(table,))
    deck = Deck(file="DeckName.pptx", title=None, slides=(slide1, slide2))

    md = MarkdownRenderer().render(deck)
    # Title falls back to file basename without extension
    assert md.startswith("# DeckName\n\n")
    # Empty table: only header appears for slide1
    assert "## Slide 1 — Untitled\n\n### Tables\n\n## Slide 2" in md
    # Ragged row: pads missing cells in second row (two empties)
    assert "| H1 | H2 | H3 |\n| --- | --- | --- |\n| A |  |  |" in md
