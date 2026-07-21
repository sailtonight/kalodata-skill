from kalodata import validate


def test_fixed_tiers():
    assert validate.check_date_range("last30Day", "rank") is None
    assert validate.check_date_range("last90Day", "rank") is not None
    assert validate.check_date_range("last90Day", "detail") is None
    assert validate.check_date_range("lastDay", "category") is not None
    assert validate.check_date_range("last7Day", "category") is None


def test_month_format():
    assert validate.check_date_range("2026-06", "rank") is None
    assert validate.check_date_range("2026-13", "rank") is not None
    assert validate.check_date_range("2026-06", "category") is not None


def test_custom_span_limits():
    assert validate.check_date_range("2026-06-01~2026-06-30", "rank") is None
    assert validate.check_date_range("2026-05-01~2026-06-30", "rank") is not None  # >31d
    assert validate.check_date_range("2026-05-01~2026-06-30", "detail") is None
    assert validate.check_date_range("2026-06-30~2026-06-01", "detail") is not None  # reversed
    assert validate.check_date_range("2026-06-01~2026-06-30", "category") is not None


def test_minmax():
    assert validate.check_minmax("0-9999", "--revenue") is None
    assert validate.check_minmax("10.5-99.9", "--price") is None
    assert validate.check_minmax("-300", "--revenue") is not None
    assert validate.check_minmax("50000-", "--revenue") is not None
