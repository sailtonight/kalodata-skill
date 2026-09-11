"""`kalo credit` — balance and consumption log."""

from __future__ import annotations

import datetime
import json

from .. import api, render, validate
from ..core import Command, Flag
from ..errors import UsageError
from . import common

LOGS_MAX_PAGE_SIZE = 100  # upstream silently clamps here
LOOKBACK_DAYS = 180  # upstream keeps no consumption history older than this


def _span(rng: str) -> tuple[str, str]:
    """`--range` (shared vocabulary) -> the startDate/endDate pair /credit/logs wants."""
    err = validate.check_date_range(rng, "detail")
    if err:
        raise UsageError(err)
    today = datetime.date.today()
    if "~" in rng:
        lo, _, hi = rng.partition("~")
        return lo, hi
    if len(rng) == 7:  # yyyy-MM
        first = datetime.date.fromisoformat(rng + "-01")
        nxt = (first.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
        return first.isoformat(), (nxt - datetime.timedelta(days=1)).isoformat()
    days = {"lastDay": 1, "last7Day": 7, "last30Day": 30, "last90Day": 90, "last180Day": 180}
    back = days.get(rng, 30)
    return (today - datetime.timedelta(days=back - 1)).isoformat(), today.isoformat()


def balance(cfg, opts, args):
    data = api.request(cfg, "/credit/balance", {}, method="GET") or {}
    if opts.get("json"):
        render.out(json.dumps(data, ensure_ascii=False))
        return 0
    sub = data.get("subRemain")
    display = {
        "total_remain": data.get("totalRemain"),
        "main_remain": data.get("mainRemain"),
    }
    if sub is not None:  # absent means the key belongs to a main account, not a zero balance
        display["sub_remain"] = sub
    display["account"] = "sub-account key" if sub is not None else "main-account key"
    render.emit_detail("credit_balance", display)
    render.emit_help(["Run `kalo credit logs` for what the credits were spent on"])
    return 0


def logs(cfg, opts, args):
    start, end = _span(opts.get("range") or "last30Day")
    page = max(1, int(opts.get("page") or 1))
    size = validate.clamp(int(opts.get("limit") or 20), 1, LOGS_MAX_PAGE_SIZE)
    body = {"startDate": start, "endDate": end, "pageNo": page, "pageSize": size}
    if opts.get("type"):
        body["sourceType"] = opts["type"]

    data = api.request(cfg, "/credit/logs", body) or {}
    rows = data.get("data") if isinstance(data, dict) else None
    rows = rows if isinstance(rows, list) else []

    if opts.get("json"):
        render.out(json.dumps(data, ensure_ascii=False))
        return 0
    if not rows:
        render.emit_empty(
            "credit_logs",
            f"{start}~{end}" + (f", type {opts['type']}" if opts.get("type") else ""),
            [
                "Only consumption is logged — top-ups and refunds never appear here",
                f"History reaches back {LOOKBACK_DAYS} days at most",
            ],
        )
        return 0

    display = [
        {
            "date": common.ms_date(r.get("gmtCreated")),
            "type": r.get("sourceType"),
            "credits": r.get("displayQuantity"),
            "product": r.get("kaloBizName"),
            "consumer_id": r.get("consumerId"),
        }
        for r in rows
    ]
    render.emit_table("credit_logs", display, ("date", "type", "credits", "product", "consumer_id"))
    spent = sum(float(r.get("displayQuantity") or 0) for r in rows)
    hints = [f"{len(rows)} of {data.get('total', len(rows))} entries, {round(-spent, 2)} credits on this page"]
    if data.get("hasNext"):
        hints.append(f"More entries: add `--page {page + 1}`")
    hints.append("Filter with `--type` using a sourceType value seen in the output")
    render.emit_help(hints)
    return 0


COMMANDS = [
    Command(
        path="credit balance",
        summary="Remaining credits on the account this key belongs to",
        handler=balance,
        examples=["kalo credit"],
    ),
    Command(
        path="credit logs",
        summary="What credits were spent on, newest first",
        handler=logs,
        flags=[
            Flag(
                "--range",
                f"date window: {validate.tier_hint('detail')} (max {LOOKBACK_DAYS} days back)",
                default="last30Day",
                metavar="RANGE",
            ),
            Flag("--type", "filter by sourceType, e.g. OPEN_API_CALL", metavar="TYPE"),
            Flag("--page", "page number", kind="int", default=1),
            Flag("--limit", f"entries per page (max {LOGS_MAX_PAGE_SIZE})", kind="int", default=20),
        ],
        examples=[
            "kalo credit logs --range last7Day",
            "kalo credit logs --range 2026-08-01~2026-08-31 --type OPEN_API_CALL",
        ],
    ),
]
