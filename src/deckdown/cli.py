from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from deckdown.extractors.text import TextExtractor
from deckdown.io import OutputManager
from deckdown.loader import Loader
from deckdown.renderers.markdown import MarkdownRenderer
from deckdown.extractors.ast import AstExtractor
from deckdown.validate import MarkdownValidator

# Exit codes (align with implementation plan)
EXIT_OK = 0
EXIT_USAGE = 2
EXIT_INPUT_ERROR = 3


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="deckdown",
        add_help=True,
        description="Extract PPTX decks to Markdown (MVP).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_extract = sub.add_parser(
        "extract",
        help="Extract deck to Markdown",
        description="Extract a .pptx deck and write Markdown output.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=(
            "Examples:\n"
            "  deckdown extract deck.pptx\n"
            "  deckdown extract deck.pptx --md-out out.md\n"
            "  deckdown extract deck.pptx --md-out out_dir/\n"
        ),
    )
    p_extract.add_argument("input", metavar="INPUT.pptx", help="Path to input .pptx file")
    p_extract.add_argument(
        "--md-out",
        dest="md_out",
        metavar="PATH_OR_DIR",
        help=(
            "Output path or directory. If a directory, writes <basename>.md inside.\n"
            "Default: alongside input as <basename>.md"
        ),
        default=None,
    )
    p_extract.add_argument(
        "--with-notes",
        action="store_true",
        help="Include speaker notes (stub; ignored for now)",
    )

    p_validate = sub.add_parser(
        "validate",
        help="Validate a markdown file containing deckdown JSON blocks",
    )
    p_validate.add_argument("input", metavar="INPUT.md", help="Path to input .md file")

    return parser


def _cmd_extract(args: argparse.Namespace) -> int:
    in_path = Path(args.input)
    if not in_path.exists():
        print(f"error: input not found: {in_path}", file=sys.stderr)
        return EXIT_INPUT_ERROR
    if in_path.is_dir():
        print(
            f"error: input is a directory, expected a .pptx file: {in_path}",
            file=sys.stderr,
        )
        return EXIT_INPUT_ERROR

    output = OutputManager()
    output_path = output.resolve_markdown_output_path(in_path, args.md_out)

    prs = Loader(str(in_path)).presentation()
    extractor = TextExtractor(with_notes=bool(args.with_notes))
    deck = extractor.extract_deck(prs, source_path=str(in_path))

    # Build AST per slide (authoritative positional data)
    ast_docs = AstExtractor().extract(prs)
    # Convert SlideDoc models to plain dicts for JSON dump
    ast_dicts = {i: doc.model_dump(mode="python") for i, doc in ast_docs.items()}

    markdown_text = MarkdownRenderer().render(deck, ast_per_slide=ast_dicts)

    output.write_text_file(output_path, markdown_text)
    return EXIT_OK


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    ns = parser.parse_args(list(argv) if argv is not None else None)

    if ns.command == "extract":
        return _cmd_extract(ns)
    if ns.command == "validate":
        in_path = Path(ns.input)
        if not in_path.exists() or in_path.is_dir():
            print(f"error: input markdown not found: {in_path}", file=sys.stderr)
            return EXIT_INPUT_ERROR
        errs = MarkdownValidator().validate_file(in_path)
        if errs:
            for e in errs:
                print(f"validate: {e}", file=sys.stderr)
            return 6
        return EXIT_OK
    # Future subcommands can be added here.
    return EXIT_USAGE  # pragma: no cover (argparse enforces subcommands)


if __name__ == "__main__":  # pragma: no cover - manual execution path
    raise SystemExit(main())
