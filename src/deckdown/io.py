from __future__ import annotations

from pathlib import Path


class OutputManager:
    def default_md_out(self, input_path: Path) -> Path:
        base = input_path.name
        name = base[:-5] if base.lower().endswith(".pptx") else base
        return input_path.with_name(f"{name}.md")

    def resolve_md_out(self, input_path: Path, md_out_opt: str | None) -> Path:
        if md_out_opt is None:
            return self.default_md_out(input_path)
        dest = Path(md_out_opt)
        if dest.exists() and dest.is_dir():
            return dest / self.default_md_out(input_path).name
        as_str = str(dest)
        if as_str.endswith("/") or as_str.endswith("\\"):
            d = Path(as_str.rstrip("/\\"))
            return d / self.default_md_out(input_path).name
        if not dest.exists() and dest.suffix.lower() != ".md":
            return dest / self.default_md_out(input_path).name
        return dest

    def write_text(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

