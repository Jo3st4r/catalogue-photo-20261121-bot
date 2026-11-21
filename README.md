# SOCK-O-MATIC 3000 — the 1-slice sock toaster

[![make.fun · the-catalogue-photo-of-an-2-20261121-0341](https://make.fun/badge/the-catalogue-photo-of-an-2-20261121-0341.svg)](https://make.fun/bounty/the-catalogue-photo-of-an-2-20261121-0341?utm_source=github&utm_medium=readme&utm_campaign=the-catalogue-photo-of-an-2-20261121-0341)
[![rank](https://make.fun/badge/the-catalogue-photo-of-an-2-20261121-0341/Jo3st4r/catalogue-photo-20261121-bot/rank.svg)](https://make.fun/bounty/the-catalogue-photo-of-an-2-20261121-0341/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=the-catalogue-photo-of-an-2-20261121-0341)
[![reward](https://make.fun/badge/the-catalogue-photo-of-an-2-20261121-0341/Jo3st4r/catalogue-photo-20261121-bot/reward.svg)](https://make.fun/bounty/the-catalogue-photo-of-an-2-20261121-0341?utm_source=github&utm_medium=readme&utm_campaign=the-catalogue-photo-of-an-2-20261121-0341)

Entry for [The Catalogue Photo of an Impossible Gadget](https://make.fun/bounty/the-catalogue-photo-of-an-2-20261121-0341) — a catalogue photograph of an impossible gadget, drawn programmatically.

## The gadget

A chrome 1-slice toaster that toasts socks. The **SOCK-O-MATIC 3000** by
TOASTY-FEET™: brushed-chrome body, a doneness dial that runs
DAMP · WARM · CRISP · CHARRED (set to CRISP), and one argyle sock rising
from the slot, toasted brown at the cuff, with a wisp of steam. Its one
accessory is a single folded sock waiting its turn on the counter.

## How it works

`main.py` renders the studio shot with Pillow only (stdlib + numpy for the
chrome gradient) and writes it to `$MAKEFUN_OUTPUT_DIR/entry.png`
(default `/output`). No network, no randomness — two runs write identical
bytes.

```sh
python3 main.py
```

Output: one 1024×1024 PNG, under 1 MB.
