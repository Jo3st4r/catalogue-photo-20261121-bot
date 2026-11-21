"""SOCK-O-MATIC 3000 — catalogue photo of an impossible gadget.

Writes /output/entry.png: a studio product shot of a chrome toaster
toasting a sock, with one folded sock as its accessory. Deterministic.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools.render import render


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    im = render()
    im.save(os.path.join(out_dir, "entry.png"), format="PNG")
    print("saved", os.path.join(out_dir, "entry.png"))


if __name__ == "__main__":
    main()
