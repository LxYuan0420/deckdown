from __future__ import annotations

from pathlib import Path


class OutputManager:
    def derive_markdown_path_next_to_input(self, input_path: Path) -> Path:
        base = input_path.name
        name = base[:-5] if base.lower().endswith(".pptx") else base
        return input_path.with_name(f"{name}.md")

    def resolve_markdown_output_path(self, input_path: Path, output_opt: str | Path | None) -> Path:
        if output_opt is None:
            return self.derive_markdown_path_next_to_input(input_path)

        dest = Path(output_opt)
        directory_hint = self._is_directory_hint(str(output_opt))
        treat_as_dir = (
            directory_hint
            or self._is_existing_directory(dest)
            or self._should_treat_as_directory(dest)
        )
        return dest / self._markdown_filename(input_path) if treat_as_dir else dest

    def write_text_file(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def _is_directory_hint(self, s: str) -> bool:
        return s.endswith("/") or s.endswith("\\")

    def _path_for_directory_hint(self, hint: str, input_path: Path) -> Path:
        directory = Path(hint.rstrip("/\\"))
        return directory / self._markdown_filename(input_path)

    def _is_existing_directory(self, p: Path) -> bool:
        return p.exists() and p.is_dir()

    def _should_treat_as_directory(self, p: Path) -> bool:
        return (not p.exists()) and (p.suffix.lower() != ".md")

    def _markdown_filename(self, input_path: Path) -> str:
        return self.derive_markdown_path_next_to_input(input_path).name
