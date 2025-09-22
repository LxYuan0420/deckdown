from __future__ import annotations

from deckdown.models import Bullet, Deck, Slide, Table, TextBlock
from deckdown.renderers.markdown import MarkdownRenderer


class TestMarkdownRenderer:
    def test_basic(self) -> None:
        # Arrange
        tb = TextBlock(text="Alpha\nBeta")
        bullets = (
            Bullet(level=0, text="Item 1"),
            Bullet(level=1, text="Sub 1"),
        )
        table = Table(rows=(("H1", "H2"), ("A|A", "B\nB")))
        slide = Slide(index=1, title="Intro", text_blocks=(tb,), bullets=bullets, tables=(table,))
        deck = Deck(file="sample.pptx", title="Sample", slides=(slide,))
        # Act
        out = MarkdownRenderer().render(deck)
        # Assert
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
        assert out == expected

    def test_renderer_class_instance(self) -> None:
        # Arrange
        slide = Slide(
            index=1,
            title="Intro",
            text_blocks=(TextBlock(text="A"),),
            bullets=(),
            tables=(),
        )
        deck = Deck(file="sample.pptx", title="Sample", slides=(slide,))
        renderer = MarkdownRenderer()
        # Act
        out = renderer.render(deck)
        # Assert
        assert out.startswith("# sample\n\n## Slide 1 — Intro\n")

    def test_empty_and_ragged_tables_and_title_fallback(self) -> None:
        # Arrange
        slide1 = Slide(index=1, title=None, text_blocks=(), bullets=(), tables=(Table(rows=()),))
        table = Table(rows=(("H1", "H2", "H3"), ("A",)))
        slide2 = Slide(index=2, title="T", text_blocks=(), bullets=(), tables=(table,))
        deck = Deck(file="DeckName.pptx", title=None, slides=(slide1, slide2))
        # Act
        md = MarkdownRenderer().render(deck)
        # Assert
        assert md.startswith("# DeckName\n\n")
        assert "## Slide 1 — Untitled\n\n### Tables\n\n## Slide 2" in md
        assert "| H1 | H2 | H3 |\n| --- | --- | --- |\n| A |  |  |" in md
