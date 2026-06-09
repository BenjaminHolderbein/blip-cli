#!/usr/bin/env python3
"""Zero-install launcher for blip-cli.

Lets the Claude Code skill (and you) run the tool straight from a checkout
without `pip install`:

    python blip_send.py list
    python blip_send.py send --to "MacBook Pro" ./report.pdf
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from blip_cli.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
