"""SOCK-O-MATIC 3000 — entry point.

Writes the catalogue photo to $MAKEFUN_OUTPUT_DIR/entry.png (default /output).
Stdlib + PIL only, deterministic, no network.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools.render import render


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    img = render()
    img.save(os.path.join(out_dir, "entry.png"), format="PNG", optimize=True)


if __name__ == "__main__":
    main()
