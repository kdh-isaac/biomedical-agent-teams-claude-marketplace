#!/usr/bin/env python3
"""Export a BMAT bundle as a local Markdown workbench."""

from __future__ import annotations

import argparse
from pathlib import Path

import bmat_run


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export BMAT bundle artifacts to a Markdown workbench.")
    parser.add_argument("--bundle", type=Path, required=True, help="Directory containing BMAT bundle artifacts.")
    parser.add_argument("--format", choices=["markdown"], default="markdown")
    parser.add_argument("--out", type=Path, help="Optional destination markdown file or directory.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing exported files.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    reports = bmat_run.export_markdown_workbench(args.bundle, args.force)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        if args.out.suffix.lower() == ".md":
            index = reports / "index.md"
            if args.out.exists() and not args.force:
                raise FileExistsError(f"{args.out} exists; use --force to overwrite")
            args.out.write_text(index.read_text(encoding="utf-8"), encoding="utf-8")
            print(f"BMAT markdown workbench index exported: {args.out.resolve()}")
        else:
            args.out.mkdir(parents=True, exist_ok=True)
            for source in reports.glob("*.md"):
                target = args.out / source.name
                if target.exists() and not args.force:
                    raise FileExistsError(f"{target} exists; use --force to overwrite")
                target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            print(f"BMAT markdown workbench exported: {args.out.resolve()}")
    else:
        print(f"BMAT markdown workbench exported: {reports.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
