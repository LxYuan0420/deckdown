from __future__ import annotations

from deckdown.models import Deck, Slide, TextBlock
from deckdown.renderers.markdown import MarkdownRenderer


def test_renderer_includes_ast_block_when_provided() -> None:
    # Arrange
    slide = Slide(index=1, title="T", text_blocks=(TextBlock(text="A"),))
    deck = Deck(file="s.pptx", title=None, slides=(slide,))
    ast = {
        1: {
            "version": "deckdown-1",
            "slide": {"index": 1, "size": {"width_emu": 1, "height_emu": 1}, "shapes": []},
        }
    }
    # Act
    md = MarkdownRenderer().render(deck, ast_per_slide=ast)
    # Assert
    assert "```json" in md and md.strip().endswith("```")
    assert '"version": "deckdown-1"' in md
