import json
import time

import pytest
from kalodata import config, update
from kalodata.cli import main


@pytest.fixture
def state(monkeypatch, tmp_path):
    """Isolate the cache file and stop any real subprocess/network from firing."""
    monkeypatch.setenv("KALODATA_CONFIG_DIR", str(tmp_path))
    monkeypatch.delenv("KALODATA_NO_UPDATE_CHECK", raising=False)
    monkeypatch.delenv("KALODATA_UPDATE_INTERVAL", raising=False)
    spawned = []
    monkeypatch.setattr(update, "_spawn_refresh", lambda: spawned.append(time.time()))
    monkeypatch.setattr(update, "__version__", "0.1.0")
    return spawned


def write_state(**kw):
    update._write_state(kw)


@pytest.mark.parametrize(
    "tag,expected",
    [
        ("v1.2.3", (1, 2, 3)),
        ("1.2", (1, 2)),
        ("0.10.0", (0, 10, 0)),
        ("v2.0.0-rc1", None),
        ("nightly", None),
        ("", None),
    ],
)
def test_parse_version(tag, expected):
    assert update.parse_version(tag) == expected


def test_newer_tag_beats_string_compare():
    assert update.parse_version("0.10.0") > update.parse_version("0.9.0")


def test_notifies_once_then_debounces(state, capsys):
    write_state(checked_at=time.time(), latest="v0.2.0")
    assert update.check(config.load()) is not None
    out = capsys.readouterr()
    assert out.out == ""  # stdout stays clean for the agent
    assert "0.1.0 → v0.2.0" in out.err
    assert update.check(config.load()) is None  # second run inside the hour is silent


def test_notifies_again_after_interval(state, monkeypatch, capsys):
    now = time.time()
    write_state(checked_at=now, notified_at=now - 3601, latest="v0.2.0")
    assert update.check(config.load()) is not None


def test_same_or_older_tag_is_silent(state, capsys):
    write_state(checked_at=time.time(), latest="v0.1.0")
    assert update.check(config.load()) is None
    assert capsys.readouterr().err == ""


def test_stale_cache_spawns_one_refresh_and_claims_the_slot(state):
    write_state(checked_at=time.time() - 7200, latest="v0.1.0")
    update.check(config.load())
    assert len(state) == 1
    update.check(config.load())  # concurrent run sees the fresh checked_at
    assert len(state) == 1


def test_fresh_cache_does_not_refresh(state):
    write_state(checked_at=time.time(), latest="v0.1.0")
    update.check(config.load())
    assert state == []


def test_disabled_by_env(state, monkeypatch, capsys):
    monkeypatch.setenv("KALODATA_NO_UPDATE_CHECK", "1")
    write_state(checked_at=time.time() - 7200, latest="v0.2.0")
    assert update.check(config.load()) is None
    assert state == []
    assert capsys.readouterr().err == ""


def test_disabled_by_config_file(state, monkeypatch, capsys):
    monkeypatch.setenv("KALODATA_UPDATE_CHECK", "false")
    write_state(checked_at=time.time() - 7200, latest="v0.2.0")
    assert update.check(config.load()) is None
    assert state == []


def test_corrupt_state_file_is_survivable(state):
    update.state_path().write_text("{not json", encoding="utf-8")
    assert update.check(config.load()) is None


def test_refresh_records_checked_at_even_when_github_fails(state, monkeypatch):
    def boom(timeout=5.0):
        raise OSError("no network")

    monkeypatch.setattr(update, "fetch_latest_tag", boom)
    update.refresh()
    data = json.loads(update.state_path().read_text())
    assert data["checked_at"] > 0
    assert "latest" not in data


def test_refresh_picks_the_highest_numeric_tag(state, monkeypatch):
    monkeypatch.setattr(
        update, "_urlopen_json", lambda url, timeout: [
            {"name": "v0.9.0"}, {"name": "v0.10.0"}, {"name": "nightly"},
        ]
    )
    assert update.fetch_latest_tag() == "v0.10.0"


def test_cli_never_fails_when_update_check_raises(env, monkeypatch, capsys):
    monkeypatch.setattr(update, "_read_state", lambda: (_ for _ in ()).throw(RuntimeError("x")))
    assert main(["--version"]) == 0
    assert "kalo" in capsys.readouterr().out


def test_current_version_is_comparable():
    """A malformed __version__ would silently disable every comparison."""
    from kalodata import __version__ as v

    assert update.parse_version(v) is not None, f"__version__ {v!r} must be numeric, and must be bumped in lockstep with the git tag"
