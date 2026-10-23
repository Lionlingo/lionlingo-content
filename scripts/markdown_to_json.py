#!/usr/bin/env python3
"""Convert the markdown curriculum into LionLingo JSON."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from contentlib import build_json  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Markdown project root (contains Exercise, Notes, Starter-Kit, Grammar-Snippets)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("dist"),
        help="Directory for generated JSON",
    )
    args = parser.parse_args()
    out = args.out if args.out.is_absolute() else Path.cwd() / args.out
    counts = build_json(args.root, out)
    print(
        "Converted "
        f"{counts['exercise_items']} exercise sentences in {counts['exercises']} lessons, "
        f"{counts['starter_items']} starter-kit sentences, "
        f"{counts['notes']} notes, "
        f"{counts['snippets']} grammar snippets"
    )
    print(f"JSON written to {out}")


if __name__ == "__main__":
    main()
