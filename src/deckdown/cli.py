from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from deckdown.models import Deck
from deckdown.renderers.markdown import MarkdownRenderer

# Exit codes (align with implementation plan)
EXIT_OK = 0
EXIT_USAGE = 2
EXIT_INPUT_ERROR = 3


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="deckdown", add_help=True)
    sub = parser.add_subparsers(dest="command", required=True)

    p_extract = sub.add_parser("extract", help="Extract deck to Markdown")
    p_extract.add_argument("input", help="Path to input .pptx file")
    p_extract.add_argument(
        "--md-out",
        dest="md_out",
        help="Path to write Markdown (default: <basename>.md)",
        default=None,
    )
    p_extract.add_argument(
        "--with-notes",
        action="store_true",
        help="Include speaker notes (stub; ignored for now)",
    )

    return parser


def _default_md_out(input_path: Path) -> Path:
    base = input_path.name
    name = base[:-5] if base.lower().endswith(".pptx") else base
    return input_path.with_name(f"{name}.md")


def _cmd_extract(args: argparse.Namespace) -> int:
    in_path = Path(args.input)
    if not in_path.is_file():
        print(f"error: input not found: {in_path}", file=sys.stderr)
        return EXIT_INPUT_ERROR

    md_out = Path(args.md_out) if args.md_out else _default_md_out(in_path)

    # Placeholder: construct an empty Deck; extractors will populate later.
    deck = Deck(file=str(in_path), title=None, slides=())
    md = MarkdownRenderer().render(deck)

    md_out.write_text(md, encoding="utf-8")
    return EXIT_OK


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    ns = parser.parse_args(list(argv) if argv is not None else None)

    if ns.command == "extract":
        return _cmd_extract(ns)
    # Future subcommands can be added here.
    return EXIT_USAGE  # pragma: no cover (argparse enforces subcommands)


if __name__ == "__main__":  # pragma: no cover - manual execution path
    raise SystemExit(main())
