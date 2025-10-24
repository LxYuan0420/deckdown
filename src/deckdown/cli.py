from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
import logging
from pathlib import Path

from deckdown.extractors.text import TextExtractor
from deckdown.io import OutputManager
from deckdown.loader import Loader
from deckdown.media import AssetStore, MediaEmbedMode
from deckdown.renderers.markdown import MarkdownRenderer
from deckdown.extractors.ast import AstExtractor
from deckdown.validate import MarkdownValidator
from deckdown.reader import MarkdownReader
from deckdown.assemble import DeckAssembler
from deckdown.preview.html import HtmlPreviewRenderer

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
    p_extract.add_argument(
        "--log-level",
        dest="log_level",
        choices=["debug", "info", "warning", "error"],
        default="info",
        help="Logging level for extraction diagnostics (default: info)",
    )
    p_extract.add_argument(
        "--embed-media",
        dest="embed_media",
        choices=["base64", "refs"],
        default="base64",
        help="Picture media embedding strategy (default: base64)",
    )

    p_validate = sub.add_parser(
        "validate",
        help="Validate a markdown file containing deckdown JSON blocks",
    )
    p_validate.add_argument("input", metavar="INPUT.md", help="Path to input .md file")

    p_assemble = sub.add_parser(
        "assemble",
        help="Assemble a PPTX from a markdown file containing deckdown JSON blocks",
    )
    p_assemble.add_argument("input", metavar="INPUT.md", help="Path to input .md file")
    p_assemble.add_argument("-o", "--output", dest="output", required=True, help="Output PPTX path")
    p_assemble.add_argument(
        "--log-level",
        dest="log_level",
        choices=["debug", "info", "warning", "error"],
        default="info",
        help="Logging level for assemble diagnostics (default: info)",
    )

    p_preview = sub.add_parser(
        "preview",
        help="Render an HTML preview from a markdown file containing deckdown JSON blocks",
    )
    p_preview.add_argument("input", metavar="INPUT.md", help="Path to input .md file")
    p_preview.add_argument("-o", "--output", dest="output", required=True, help="Output HTML path")

    p_schema = sub.add_parser(
        "schema",
        help="Print JSON Schema for the per-slide AST (SlideDoc)",
    )
    p_schema.add_argument(
        "-o", "--output", dest="output", help="Output path (writes to stdout if omitted)"
    )

    return parser


def _cmd_extract(args: argparse.Namespace) -> int:
    logging.basicConfig(level=getattr(logging, str(args.log_level).upper(), logging.INFO))
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
    media_mode: MediaEmbedMode = getattr(args, "embed_media", "base64")
    asset_store = AssetStore(output_path) if media_mode == "refs" else None

    prs = Loader(str(in_path)).presentation()
    extractor = TextExtractor(with_notes=bool(args.with_notes))
    deck = extractor.extract_deck(prs, source_path=str(in_path))

    # Build AST per slide (authoritative positional data)
    ast_docs = AstExtractor(media_mode=media_mode, asset_store=asset_store).extract(prs)
    # Convert SlideDoc models to plain dicts for JSON dump
    ast_dicts = {i: doc.model_dump(mode="python") for i, doc in ast_docs.items()}
    # Tiny diagnostics
    shape_counts: dict[str, int] = {}
    for doc in ast_docs.values():
        for sh in doc.slide.shapes:
            shape_counts[sh.kind.value] = shape_counts.get(sh.kind.value, 0) + 1
    logging.info("extracted %d slides; shapes=%s", len(ast_docs), shape_counts)

    markdown_text = MarkdownRenderer().render(
        deck,
        ast_per_slide=ast_dicts,
    )

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
    if ns.command == "assemble":
        logging.basicConfig(
            level=getattr(logging, str(getattr(ns, "log_level", "info")).upper(), logging.INFO)
        )
        in_path = Path(ns.input)
        out_path = Path(ns.output)
        if not in_path.exists() or in_path.is_dir():
            print(f"error: input markdown not found: {in_path}", file=sys.stderr)
            return EXIT_INPUT_ERROR
        docs = MarkdownReader().load_file(in_path)
        # tiny metrics
        slide_ct = len(docs)
        shape_ct = sum(len(d.slide.shapes) for d in docs)
        logging.info("assemble input: slides=%d shapes=%d", slide_ct, shape_ct)
        DeckAssembler().assemble(docs, out=out_path)
        return EXIT_OK
    if ns.command == "preview":
        in_path = Path(ns.input)
        out_path = Path(ns.output)
        if not in_path.exists() or in_path.is_dir():
            print(f"error: input markdown not found: {in_path}", file=sys.stderr)
            return EXIT_INPUT_ERROR
        docs = MarkdownReader().load_file(in_path)
        html = HtmlPreviewRenderer().render_deck(docs)
        out_path.write_text(html, encoding="utf-8")
        return EXIT_OK
    if ns.command == "schema":
        from deckdown.ast import SlideDoc
        import json

        schema = SlideDoc.model_json_schema()
        text = json.dumps(schema, ensure_ascii=False, indent=2, sort_keys=False)
        out = getattr(ns, "output", None)
        if out:
            Path(out).write_text(text, encoding="utf-8")
        else:
            print(text)
        return EXIT_OK
    # Future subcommands can be added here.
    return EXIT_USAGE  # pragma: no cover (argparse enforces subcommands)


if __name__ == "__main__":  # pragma: no cover - manual execution path
    raise SystemExit(main())
