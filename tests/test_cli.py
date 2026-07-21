import json

from kalodata.cli import main


def run(capsys, *argv):
    code = main(list(argv))
    return code, capsys.readouterr().out


def test_home_without_config(capsys, monkeypatch, tmp_path):
    for var in ("KALODATA_API_KEY", "KALODATA_USER_ID", "KALODATA_BASE_URL"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("KALODATA_CONFIG_DIR", str(tmp_path))
    code, out = run(capsys)
    assert code == 0
    assert "commands[" in out
    assert "auth: not configured" in out


def test_unknown_flag_exits_2(capsys, env):
    code, out = run(capsys, "product", "rank", "--stat", "x")
    assert code == 2
    assert out.startswith("error: unknown flag --stat")
    assert "--region" in out  # valid flags inlined for one-turn self-correction


def test_renamed_flag_hint(capsys, env):
    code, out = run(capsys, "product", "rank", "--limit", "abc")
    assert code == 2
    assert "expects an integer" in out


def test_rank_happy_path(capsys, env):
    env.responses["/tiktok/product/rank"] = {
        "success": True,
        "data": [
            {
                "product_id": "111",
                "product_name": "Widget, deluxe",
                "revenue": 1234.5,
                "sales_volumn": 42,
                "unit_price": 9.99,
            }
        ],
    }
    code, out = run(capsys, "product", "rank", "--region", "US")
    assert code == 0
    assert "products[1]{product_id,product_name,revenue,sales_volumn}:" in out
    assert '"111","Widget, deluxe",1234.5,42' in out
    assert "kalo product detail" in out  # contextual disclosure
    path, headers, body = env.requests[0]
    assert headers["secret-key"] == "test-key"
    assert headers["x-user-id"] == "12345"
    assert body["sort_field"] == {"field": "revenue", "type": "DESC"}
    assert body["date_range"] == "last30Day"


def test_rank_empty_state(capsys, env):
    env.responses["/tiktok/product/rank"] = {"success": False, "message": "record not found"}
    code, out = run(capsys, "product", "rank")
    assert code == 0
    assert out.startswith("products: 0 results (region US, last30Day)")


def test_membership_error(capsys, env):
    env.responses["/tiktok/product/rank"] = {
        "success": False,
        "code": "2016",
        "message": "query count exceeded",
    }
    code, out = run(capsys, "product", "rank")
    assert code == 1
    assert "membership/quota limit" in out
    assert "Narrow --range" in out


def test_2016_parameter_misclassification(capsys, env):
    env.responses["/tiktok/product/rank"] = {
        "success": False,
        "code": "2016",
        "message": "date_range must be one of ...",
    }
    code, out = run(capsys, "product", "rank")
    assert code == 1
    assert "rejected a parameter" in out


def test_detail_trend_normalized(capsys, env):
    env.responses["/tiktok/product/detail"] = {
        "success": True,
        "data": {
            "product_id": "111",
            "product_name": "Widget",
            "revenue": 100,
            "revenue_trend": [1000, 3000, 2000],
        },
    }
    code, out = run(capsys, "product", "detail", "111")
    assert code == 0
    # trend arrives x100 -> /100, then summarized
    assert "total: 60" in out
    assert "peak: 30" in out
    body = env.requests[0][2]
    assert body["product_id"] == "111"
    assert body["need_extra"] is True


def test_detail_full_trend(capsys, env):
    env.responses["/tiktok/product/detail"] = {
        "success": True,
        "data": {"product_id": "1", "revenue_trend": [1000, 3000]},
    }
    code, out = run(capsys, "product", "detail", "1", "--full")
    assert code == 0
    assert "revenue_trend[2]: 10,30" in out


def test_shop_keyword_omits_sort(capsys, env):
    env.responses["/tiktok/shop/rank"] = {"success": True, "data": []}
    code, _ = run(capsys, "shop", "rank", "--keyword", "anker")
    assert code == 0
    assert "sort_field" not in env.requests[0][2]


def test_json_escape_hatch(capsys, env):
    env.responses["/tiktok/shop/rank"] = {
        "success": True,
        "data": [{"shop_id": "9", "shop_name": "S", "revenue": 1}],
    }
    code, out = run(capsys, "shop", "rank", "--json")
    assert code == 0
    assert json.loads(out) == [{"shop_id": "9", "shop_name": "S", "revenue": 1}]


def test_fields_flag_extends_schema(capsys, env):
    env.responses["/tiktok/creator/rank"] = {
        "success": True,
        "data": [{"creator_id": "c1", "creator_handle": "h", "revenue": 1, "creator_followers": "1000", "live_revenue": 5}],
    }
    code, out = run(capsys, "creator", "rank", "--fields", "live_revenue")
    assert code == 0
    assert "live_revenue" in out.splitlines()[0]
    assert ",1000," in out.splitlines()[1]  # string number coerced


def test_fields_flag_rejects_unknown(capsys, env):
    code, out = run(capsys, "creator", "rank", "--fields", "nope")
    assert code == 2
    assert "unknown field 'nope'" in out


def test_default_subcommand_content_first(capsys, env):
    env.responses["/tiktok/product/rank"] = {"success": True, "data": []}
    code, _ = run(capsys, "product", "--region", "GB")
    assert code == 0
    assert env.requests[0][2]["region"] == "GB"


def test_config_set_and_show(capsys, monkeypatch, tmp_path):
    for var in ("KALODATA_API_KEY", "KALODATA_USER_ID"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("KALODATA_CONFIG_DIR", str(tmp_path))
    code, out = run(capsys, "config", "set", "--key", "sk-abc123", "--user-id", "42")
    assert code == 0
    code, out = run(capsys, "config")
    assert code == 0
    assert "…c123" in out or "c123" in out
    assert "user_id: \"42\"" in out or "user_id: 42" in out
    assert "sk-abc123" not in out  # masked


def test_config_set_rejects_non_numeric_user(capsys, monkeypatch, tmp_path):
    monkeypatch.setenv("KALODATA_CONFIG_DIR", str(tmp_path))
    code, out = run(capsys, "config", "set", "--user-id", "abc")
    assert code == 2
    assert "must be numeric" in out


def test_home_lists_all_commands(capsys, monkeypatch, tmp_path):
    monkeypatch.setenv("KALODATA_CONFIG_DIR", str(tmp_path))
    code, out = run(capsys)
    assert code == 0
    assert "commands[14]" in out
    assert "kalo config" in out
