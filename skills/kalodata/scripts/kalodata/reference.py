"""Content for the no-args home view.

The SKILL.md next to this package mirrors this command table — keep both
in sync when commands change.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from . import toon
from .config import Config

DESCRIPTION = (
    "TikTok Shop e-commerce analytics from KaloData — rankings and details "
    "for products, shops, creators, videos, livestreams and categories"
)

# (command, what) — the `what` column is deliberately terse; details live in --help
COMMAND_TABLE = [
    ("kalo product rank", "top products; --category --keyword --price --launch --shop --creator"),
    ("kalo product detail <id...>", "price range, shop id, revenue trend"),
    ("kalo shop rank", "top shops; --type BRAND|RETAILER --keyword"),
    ("kalo shop detail <id...>", "revenue split, top product ids"),
    ("kalo creator rank", "top creators; --followers --engagement --product"),
    ("kalo creator detail <id|@handle...>", "contact email/handle, GPM, trend"),
    ("kalo video rank", "top shoppable videos; --product --creator --keyword --ai"),
    ("kalo video detail <id...>", "full video metrics + trend"),
    ("kalo live rank", "top livestreams; --keyword"),
    ("kalo live detail <id...>", "viewers, GPM, top product ids"),
    ("kalo category rank", "top categories; --level 1|2|3"),
    ("kalo category detail <id...>", "category revenue split + trend"),
    ("kalo category search <kw>", "resolve category ids by keyword"),
    ("kalo config", "show/set credentials and defaults"),
]

CONVENTIONS = [
    "All list commands take --region --range --page (1-5) --limit (5-100) --sort --asc --fields --json",
    "Regions: US GB ID TH VN PH MY SG JP MX DE IT FR ES BR; ranges like last7Day, last30Day, "
    "yyyy-MM, or yyyy-MM-dd~yyyy-MM-dd",
    'Numeric ranges are "min-max" with both ends numeric, e.g. --revenue 1000-50000',
    "Run `kalo <command> --help` for per-command flags and examples",
]


def bin_path() -> str:
    found = shutil.which("kalo")
    path = found or sys.argv[0] or "kalo"
    home = str(Path.home())
    if path.startswith(home):
        path = "~" + path[len(home):]
    return path


def auth_line(cfg: Config) -> str:
    if cfg.authed:
        return f"auth: ok (user {cfg.user_id})"
    return "auth: not configured — run `kalo config set --key <API_KEY> --user-id <ID>`"


def home_text(cfg: Config) -> str:
    lines = [
        f"bin: {bin_path()}",
        f"description: {DESCRIPTION}",
        auth_line(cfg),
        f"defaults: region {cfg.region} · range last30Day · currency {cfg.currency} · language {cfg.language}",
        "",
        toon.tabular("commands", [{"command": c, "what": w} for c, w in COMMAND_TABLE], ["command", "what"]),
        "",
        f"help[{len(CONVENTIONS)}]:",
    ]
    lines.extend(f"  {c}" for c in CONVENTIONS)
    return "\n".join(lines)
