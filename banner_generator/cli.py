from __future__ import annotations

import argparse
import sys
from pathlib import Path

from banner_generator.renderer import RenderSpec, load_spec, render


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate branded social banners from HTML templates.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    render = subparsers.add_parser("render", help="Render one JSON spec or one inline banner.")
    render.add_argument("spec", nargs="?", type=Path, help="Path to a JSON render spec.")
    render.add_argument("--template", help="Bundled template name or path to an HTML template.")
    render.add_argument("--template-dir", type=Path, help="Directory with custom templates.")
    render.add_argument("--size", help="Named size: og, wide, square, linkedin.")
    render.add_argument("--format", choices=["png", "jpeg", "pdf"], help="Output format.")
    render.add_argument("--quality", type=int, help="JPEG quality, from 0 to 100.")
    render.add_argument("--width", type=int, help="Custom viewport width.")
    render.add_argument("--height", type=int, help="Custom viewport height.")
    render.add_argument("--output", type=Path, help="Output file path.")
    render.add_argument("--html-output", type=Path, help="Optional rendered HTML debug output.")
    render.add_argument("--title", help="Banner title.")
    render.add_argument("--subtitle", help="Banner subtitle.")
    render.add_argument("--label", help="Small content label.")
    render.add_argument("--meta", help="Date, author, or other metadata.")
    render.add_argument("--brand", help="Brand text.")
    render.add_argument("--accent", help="Small accent text.")

    return parser


def spec_from_args(args: argparse.Namespace) -> RenderSpec:
    if args.spec:
        spec = load_spec(args.spec)
        output = args.output or spec.output
        return RenderSpec(
            template=args.template or spec.template,
            output=output,
            size=args.size or spec.size,
            format=args.format or spec.format,
            quality=args.quality or spec.quality,
            data=spec.data,
            width=args.width or spec.width,
            height=args.height or spec.height,
        )

    if not args.template or not args.output:
        raise SystemExit("Either provide a JSON spec, or provide both --template and --output.")

    data = {
        "title": args.title,
        "subtitle": args.subtitle,
        "label": args.label,
        "meta": args.meta,
        "brand": args.brand,
        "accent": args.accent,
    }
    return RenderSpec(
        template=args.template,
        output=args.output,
        size=args.size or "og",
        format=args.format,
        quality=args.quality,
        data={key: value for key, value in data.items() if value is not None},
        width=args.width,
        height=args.height,
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "render":
        spec = spec_from_args(args)
        output = render(spec, template_dir=args.template_dir, html_output=args.html_output)
        print(output)
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
