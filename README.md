# kalodata-skill

Agent skill for [KaloData](https://www.kalodata.com) TikTok Shop analytics — rankings, details and revenue trends for products, shops, creators, videos, livestreams and categories.

The skill bundles a zero-dependency CLI (`kalo`, Python 3.11+ stdlib only). Installing the skill is all it takes: the agent runs the CLI straight from the skill directory.

## Install

```sh
npx skills add Kalodata/kalodata-skill               # project-level
npx skills add Kalodata/kalodata-skill -g            # global
```

## Configure

```sh
export KALODATA_API_KEY=<api-key>
export KALODATA_USER_ID=<numeric-user-id>
```

Or persist with `kalo config set --key <api-key> --user-id <id>`. Optional: `KALODATA_BASE_URL` (defaults to production), `KALODATA_REGION` / `KALODATA_LANGUAGE` / `KALODATA_CURRENCY`.

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
| `kalo category search <kw>` | Resolve category ids by keyword |
| `kalo config [set]` | Show or save credentials and defaults |

Nouns: `product` · `shop` · `creator` · `video` · `live` · `category`. All list commands accept `--region --range --page --limit --sort --asc --fields --json`; see `kalo <command> --help` for details. Exit codes: `0` success, `1` error, `2` usage error.

## Development

```sh
uv run --with pytest pytest -q     # tests run against a local mock server, no credentials needed
```

## License

MIT
