# kalodata-skill

Agent skill for [KaloData](https://www.kalodata.com) TikTok Shop analytics — rankings, details and revenue trends for products, shops, creators, videos, livestreams and categories.

The skill bundles a zero-dependency CLI (`kalo`, Python 3.11+ stdlib only). Installing the skill is all it takes: the agent runs the CLI straight from the skill directory.

## Install

```sh
npx skills add sailtonight/kalodata-skill               # project-level
npx skills add sailtonight/kalodata-skill -g            # global
```

## Configure

Get a key at [open-center/account](https://www.kalodata.com/open-center/account) → *generate key* (register at [open-center/home](https://www.kalodata.com/open-center/home) first if you have no account). Already calling the KaloData API on credit-based billing? That same key works here.

```sh
export KALODATA_API_KEY=<token>
```

Or persist with `kalo config set --key <token>`. The token is sent as the `secret-key` header. Optional: `KALODATA_BASE_URL` (defaults to production), `KALODATA_REGION` / `KALODATA_LANGUAGE` / `KALODATA_CURRENCY`.

Queries spend KaloData credits — 0.2 for a basic lookup, 0.01–1 for media URLs and review insight, 1–2 for an analysis/diagnosis. `kalo credit` shows the remaining balance and `kalo credit logs` what it went on; top up at [kalodata.com/pricing](https://www.kalodata.com/pricing). Run `kalo` with no key configured and it prints this same setup guide.

### Upgrade notice

The CLI compares its version against the newest tag on GitHub and prints a one-line hint to stderr when a newer one exists, leaving stdout clean for the agent. The check runs in a detached background process, so it never adds latency, and both the GitHub request and the hint itself are debounced to once an hour. Turn it off with `KALODATA_NO_UPDATE_CHECK=1` or `kalo config set --update-check off`.

## Usage

```sh
alias kalo="python3 skills/kalodata/scripts/kalo.py"

kalo                                          # command map + auth status
kalo product rank --region US --range last7Day
kalo product detail 1729508370969629931
kalo creator rank --followers 10000-1000000
kalo video rank --product <product_id>
kalo category search beauty
```

Output is token-efficient TOON; add `--json` for raw JSON:

```
products[5]{product_id,product_name,revenue,sales_volumn}:
  "1732263142232921043",Voyage Nova | Rosey Fruity Floral | Extrait De …,597981,26472
  ...
help[3]:
  Run `kalo product detail <product_id>` for price range, shop id, revenue trend
  ...
```

## Commands

| Command | Description |
|---|---|
| `kalo <noun> rank` | Ranked lists with filters (`--category`, `--keyword`, `--price`, `--followers`, …) |
| `kalo <noun> detail <id...>` | Full metrics for one or more ids, revenue trend included |
| `kalo product comments <id...>` | Review insight: pain points, positives, usage scenarios |
| `kalo product specs <id...>` | Selling points and spec attributes (`--lang zh-CN` translates) |
| `kalo product images <id...>` / `kalo creator images <id...>` / `kalo video url <id...>` | Signed media URLs, ~5 min expiry |
| `kalo category search <kw>` | Resolve category ids by keyword |
| `kalo credit [logs]` | Credit balance and consumption log |
| `kalo config [set]` | Show or save credentials and defaults |

Nouns: `product` · `shop` · `creator` · `video` · `live` · `category`. All list commands accept `--region --range --page --limit --sort --asc --fields --json`; see `kalo <command> --help` for details. Exit codes: `0` success, `1` error, `2` usage error.

## Development

```sh
uv run --with pytest pytest -q     # tests run against a local mock server, no credentials needed
```

## License

MIT
