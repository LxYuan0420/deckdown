from __future__ import annotations

from dataclasses import dataclass, field
from mimetypes import guess_extension
from pathlib import Path
from typing import Literal

MediaEmbedMode = Literal["base64", "refs"]


def _extension_for(content_type: str) -> str:
    ext = guess_extension(content_type or "")
    if ext in {".jpe", ".jpeg"}:
        return ".jpg"
    if ext:
        return ext
    if content_type == "image/jpeg":
        return ".jpg"
    if content_type == "image/png":
        return ".png"
    if content_type == "image/gif":
        return ".gif"
    return ".bin"


@dataclass
class AssetStore:
    markdown_path: Path
    asset_dir_name_suffix: str = "_assets"
    filename_prefix: str = "image"
    _counter: int = field(default=0, init=False, repr=False)

    def __post_init__(self) -> None:
        self.markdown_path = Path(self.markdown_path)
        self._root_dir = self.markdown_path.parent
        stem = self.markdown_path.stem
        self._assets_dir = self._root_dir / f"{stem}{self.asset_dir_name_suffix}"

    @property
    def assets_dir(self) -> Path:
        return self._assets_dir

    def save_image(
        self,
        *,
        blob: bytes,
        content_type: str,
        name_hint: str | None = None,
    ) -> str:
        self._ensure_directory()
        ext = _extension_for(content_type)
        base_name = self._sanitize_name(name_hint) if name_hint else self.filename_prefix
        index = self._counter
        while True:
            candidate = f"{base_name}-{index:03d}{ext}"
            path = self._assets_dir / candidate
            if not path.exists():
                break
            index += 1
        path.write_bytes(blob)
        self._counter = index + 1
        # Return path relative to markdown output parent for portability
        rel_path = Path(self._assets_dir.name) / candidate
        return str(rel_path)

    def _ensure_directory(self) -> None:
        self._assets_dir.mkdir(parents=True, exist_ok=True)

    def _sanitize_name(self, value: str) -> str:
        clean = "".join(ch for ch in value if ch.isalnum() or ch in ("-", "_"))
        return clean or self.filename_prefix
