from __future__ import annotations

import base64
from pathlib import Path
from types import SimpleNamespace

from pptx.enum.shapes import MSO_SHAPE_TYPE

from deckdown.ast import SlideSize
from deckdown.color.theme import ThemeResolver
from deckdown.extractors.context import ExtractContext
from deckdown.extractors.handlers.picture_handler import PictureShapeHandler
from deckdown.media import AssetStore

PNG_1PX = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII="
)


def _make_shape(blob: bytes) -> SimpleNamespace:
    image = SimpleNamespace(blob=blob, content_type="image/png")
    return SimpleNamespace(
        shape_type=MSO_SHAPE_TYPE.PICTURE,
        image=image,
        left=0,
        top=0,
        width=91440,
        height=91440,
        shape_id=7,
        name="Picture 1",
        crop_left=0.0,
        crop_right=0.0,
        crop_top=0.0,
        crop_bottom=0.0,
        alternative_text=None,
    )


def _context(*, media_mode: str, asset_store: AssetStore | None = None) -> ExtractContext:
    size = SlideSize(width_emu=9144000, height_emu=6858000)
    theme = ThemeResolver({"dk1": "#000000", "lt1": "#FFFFFF"})
    return ExtractContext(size=size, theme=theme, media_mode=media_mode, asset_store=asset_store)


def test_picture_handler_base64_data_url() -> None:
    shape = _make_shape(base64.b64decode(PNG_1PX))
    handler = PictureShapeHandler()
    ctx = _context(media_mode="base64", asset_store=None)

    result = handler.build(shape, z=3, ctx=ctx)

    assert result is not None
    assert result.image.media.data_url is not None
    assert result.image.media.data_url.startswith("data:image/png;base64,")
    assert result.image.media.ref is None


def test_picture_handler_refs_uses_asset_store(tmp_path: Path) -> None:
    shape = _make_shape(base64.b64decode(PNG_1PX))
    handler = PictureShapeHandler()
    markdown_path = tmp_path / "deck.md"
    asset_store = AssetStore(markdown_path)
    ctx = _context(media_mode="refs", asset_store=asset_store)

    result = handler.build(shape, z=5, ctx=ctx)

    assert result is not None
    assert result.image.media.ref is not None
    assert result.image.media.data_url is None

    ref_path = tmp_path / result.image.media.ref
    assert ref_path.exists()
    assert ref_path.suffix == ".png"
