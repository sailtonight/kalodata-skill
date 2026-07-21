#!/usr/bin/env python3
"""Entry point for the bundled kalo CLI — run directly, no install needed.

    python3 scripts/kalo.py product rank --region US
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kalodata.cli import main  # noqa: E402

sys.exit(main())
