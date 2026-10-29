"""First-run guide, shown wherever the API key turns out to be missing.

One source of truth for getting a key and saving it. The Setup section of the
SKILL.md next to this package mirrors it — keep both in sync.
"""

from __future__ import annotations

KEY_URL = "https://www.kalodata.com/open-center/account"
SIGNUP_URL = "https://www.kalodata.com/open-center/home"

SETUP_LINES = [
    f'1. Get a key: sign in at {KEY_URL} and click "generate key" '
    f"(no account yet? register at {SIGNUP_URL}). An existing KaloData Open API "
    "key works here — no new key needed.",
    "2. Save it: `kalo config set --key <API_KEY>`, or set KALODATA_API_KEY in the environment.",
    "3. Re-run your query.",
]

NO_KEY_MESSAGE = "no KaloData API key configured yet"
