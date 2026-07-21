from kalodata import toon


def test_scalar_quoting():
    assert toon.scalar("plain") == "plain"
    assert toon.scalar("a,b") == '"a,b"'
    assert toon.scalar("123") == '"123"'  # numeric-looking string stays a string
    assert toon.scalar(123) == "123"
    assert toon.scalar(None) == "null"
    assert toon.scalar(True) == "true"
    assert toon.scalar(1234.5678) == "1234.57"
    assert toon.scalar(10.0) == "10"


def test_tabular():
    rows = [{"id": "1", "title": "Fix, bug", "n": 5}, {"id": "2", "title": "ok", "n": None}]
    out = toon.tabular("tasks", rows, ["id", "title", "n"])
    assert out.splitlines() == [
        "tasks[2]{id,title,n}:",
        '  "1","Fix, bug",5',
        '  "2",ok,null',
    ]


def test_kv_nested():
    out = toon.kv("shop", {"id": "9", "stats": {"revenue": 1.5}, "top": ["a", "b"]})
    assert "shop:" in out
    assert "  id: \"9\"" in out
    assert "    revenue: 1.50" in out or "    revenue: 1.5" in out
    assert "  top[2]: a,b" in out


def test_kv_list_of_dicts():
    out = toon.kv("wrap", {"items": [{"a": 1, "b": 2}]})
    assert "items[1]{a,b}:" in out
