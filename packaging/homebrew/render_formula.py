#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render a Homebrew formula for prebuilt CoreQuarry macOS archives."
    )
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--arm64", type=Path, required=True)
    parser.add_argument("--x86-64", dest="x86_64", type=Path, required=True)
    args = parser.parse_args()

    rendered = args.template.read_text(encoding="utf-8")
    replacements = {
        "@VERSION@": args.version,
        "@TAG@": args.tag,
        "@ARM64_SHA256@": sha256(args.arm64),
        "@X86_64_SHA256@": sha256(args.x86_64),
    }
    for marker, value in replacements.items():
        rendered = rendered.replace(marker, value)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")


if __name__ == "__main__":
    main()
