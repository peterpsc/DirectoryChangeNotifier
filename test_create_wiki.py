"""
Tests for create_wiki.py helper functions.
Run:  pytest test_create_wiki.py -v
"""

import json
import uuid
import pytest

from create_wiki import (
    STORE_OPEN, STORE_CLOSE,
    _ts, _find, _load, _save,
    add_or_update, add_json_tiddler, add_todolist,
)


# ---------------------------------------------------------------------------
# _ts
# ---------------------------------------------------------------------------

def test_ts_returns_17_digit_string():
    ts = _ts()
    assert ts.isdigit()
    assert len(ts) == 17  # YYYYMMDDHHMMSSmmm


def test_ts_offsets_produce_different_values():
    ts = [_ts(i) for i in range(3)]
    assert ts[0] != ts[1] != ts[2]


def test_ts_offsets_are_ordered():
    assert _ts(0) < _ts(1) < _ts(2)


# ---------------------------------------------------------------------------
# _find
# ---------------------------------------------------------------------------

def test_find_returns_matching_tiddler():
    tiddlers = [{"title": "Foo", "text": "bar"}, {"title": "Baz", "text": "qux"}]
    assert _find(tiddlers, "Foo")["text"] == "bar"


def test_find_returns_none_when_absent():
    assert _find([], "Missing") is None
    assert _find([{"title": "Other"}], "Missing") is None


# ---------------------------------------------------------------------------
# add_or_update
# ---------------------------------------------------------------------------

def test_add_or_update_creates_new_tiddler():
    tiddlers = []
    add_or_update(tiddlers, "Title", "Text")
    assert len(tiddlers) == 1
    t = tiddlers[0]
    assert t["title"] == "Title"
    assert t["text"] == "Text"
    assert "created" in t and "modified" in t


def test_add_or_update_no_duplicate():
    tiddlers = []
    add_or_update(tiddlers, "T", "first")
    add_or_update(tiddlers, "T", "second")
    assert len(tiddlers) == 1
    assert tiddlers[0]["text"] == "second"


def test_add_or_update_tags_none_preserves_existing_tags():
    tiddlers = []
    add_or_update(tiddlers, "T", "text", tags="Contents")
    add_or_update(tiddlers, "T", "updated", tags=None)
    assert tiddlers[0]["tags"] == "Contents"


def test_add_or_update_tags_updated_when_provided():
    tiddlers = []
    add_or_update(tiddlers, "T", "text", tags="OldTag")
    add_or_update(tiddlers, "T", "text", tags="NewTag")
    assert tiddlers[0]["tags"] == "NewTag"


def test_add_or_update_spaced_tag_stored_as_single_tag():
    tiddlers = []
    add_or_update(tiddlers, "T", "text", tags="[[Peter Requests]]")
    assert tiddlers[0]["tags"] == "[[Peter Requests]]"


def test_add_or_update_new_tiddler_has_no_tags_when_omitted():
    tiddlers = []
    add_or_update(tiddlers, "T", "text")
    assert "tags" not in tiddlers[0]


# ---------------------------------------------------------------------------
# add_json_tiddler
# ---------------------------------------------------------------------------

def test_add_json_tiddler_creates_with_correct_type():
    tiddlers = []
    add_json_tiddler(tiddlers, "mytitle", {"key": "val"})
    assert len(tiddlers) == 1
    assert tiddlers[0]["type"] == "application/json"
    assert json.loads(tiddlers[0]["text"]) == {"key": "val"}


def test_add_json_tiddler_skips_when_already_present():
    tiddlers = []
    add_json_tiddler(tiddlers, "mytitle", {"key": "original"})
    add_json_tiddler(tiddlers, "mytitle", {"key": "overwrite"})
    assert len(tiddlers) == 1
    assert json.loads(tiddlers[0]["text"])["key"] == "original"


# ---------------------------------------------------------------------------
# add_todolist — first run
# ---------------------------------------------------------------------------

def test_add_todolist_first_run_creates_five_tiddlers():
    tiddlers = []
    add_todolist(tiddlers, "High", ["Task A", "Task B"])
    titles = {t["title"] for t in tiddlers}
    assert titles == {
        "$:/todolist/data/tasks/High",
        "$:/todolist/data/status/High",
        "$:/todolist/data/priority/High",
        "$:/todolist/data/done/High",
        "$:/todolist/data/state/High",
    }


def test_add_todolist_task_values_correct():
    tiddlers = []
    add_todolist(tiddlers, "High", ["Task A", "Task B"])
    tasks = json.loads(_find(tiddlers, "$:/todolist/data/tasks/High")["text"])
    assert set(tasks.values()) == {"Task A", "Task B"}


def test_add_todolist_status_all_undone():
    tiddlers = []
    add_todolist(tiddlers, "High", ["Task A", "Task B"])
    status = json.loads(_find(tiddlers, "$:/todolist/data/status/High")["text"])
    assert all(v == "undone" for v in status.values())


def test_add_todolist_priority_all_none():
    tiddlers = []
    add_todolist(tiddlers, "High", ["Task A"])
    priority = json.loads(_find(tiddlers, "$:/todolist/data/priority/High")["text"])
    assert all(v == "none" for v in priority.values())


def test_add_todolist_keys_consistent_across_tiddlers():
    tiddlers = []
    add_todolist(tiddlers, "High", ["Task A", "Task B"])
    tasks    = json.loads(_find(tiddlers, "$:/todolist/data/tasks/High")["text"])
    status   = json.loads(_find(tiddlers, "$:/todolist/data/status/High")["text"])
    priority = json.loads(_find(tiddlers, "$:/todolist/data/priority/High")["text"])
    assert set(tasks.keys()) == set(status.keys()) == set(priority.keys())


def test_add_todolist_empty_tasks_no_crash():
    tiddlers = []
    add_todolist(tiddlers, "Critical", [])
    tasks = json.loads(_find(tiddlers, "$:/todolist/data/tasks/Critical")["text"])
    assert tasks == {}


# ---------------------------------------------------------------------------
# add_todolist — subsequent runs (merge)
# ---------------------------------------------------------------------------

def test_add_todolist_merge_appends_new_task():
    tiddlers = []
    add_todolist(tiddlers, "High", ["Task A"])
    add_todolist(tiddlers, "High", ["Task A", "Task B"])
    tasks = json.loads(_find(tiddlers, "$:/todolist/data/tasks/High")["text"])
    assert set(tasks.values()) == {"Task A", "Task B"}


def test_add_todolist_merge_no_duplicate_on_same_seed():
    tiddlers = []
    add_todolist(tiddlers, "High", ["Task A", "Task B"])
    add_todolist(tiddlers, "High", ["Task A", "Task B"])
    tasks = json.loads(_find(tiddlers, "$:/todolist/data/tasks/High")["text"])
    assert len(tasks) == 2


def test_add_todolist_merge_keys_consistent_after_merge():
    tiddlers = []
    add_todolist(tiddlers, "High", ["Task A"])
    add_todolist(tiddlers, "High", ["Task A", "Task B"])
    tasks    = json.loads(_find(tiddlers, "$:/todolist/data/tasks/High")["text"])
    status   = json.loads(_find(tiddlers, "$:/todolist/data/status/High")["text"])
    priority = json.loads(_find(tiddlers, "$:/todolist/data/priority/High")["text"])
    assert set(tasks.keys()) == set(status.keys()) == set(priority.keys())


def test_add_todolist_merge_new_task_is_undone():
    tiddlers = []
    add_todolist(tiddlers, "High", ["Task A"])
    add_todolist(tiddlers, "High", ["Task A", "Task B"])
    tasks  = json.loads(_find(tiddlers, "$:/todolist/data/tasks/High")["text"])
    status = json.loads(_find(tiddlers, "$:/todolist/data/status/High")["text"])
    new_key = next(k for k, v in tasks.items() if v == "Task B")
    assert status[new_key] == "undone"


def test_add_todolist_merge_preserves_existing_status():
    tiddlers = []
    add_todolist(tiddlers, "High", ["Task A"])
    # Simulate user marking Task A done
    status_t = _find(tiddlers, "$:/todolist/data/status/High")
    existing = json.loads(status_t["text"])
    key_a = next(iter(existing))
    existing[key_a] = "done"
    status_t["text"] = json.dumps(existing)
    # Merge a new task — Task A's status must stay "done"
    add_todolist(tiddlers, "High", ["Task A", "Task B"])
    status = json.loads(_find(tiddlers, "$:/todolist/data/status/High")["text"])
    assert status[key_a] == "done"


# ---------------------------------------------------------------------------
# _load / _save round-trip
# ---------------------------------------------------------------------------

def _make_html(tiddlers):
    return f"<html>{STORE_OPEN}{json.dumps(tiddlers)}{STORE_CLOSE}</html>"


def test_load_parses_tiddlers(tmp_path):
    p = tmp_path / "wiki.html"
    p.write_text(_make_html([{"title": "T", "text": "hello"}]), encoding="utf-8")
    _, tiddlers, _, _ = _load(str(p))
    assert tiddlers[0]["title"] == "T"
    assert tiddlers[0]["text"] == "hello"


def test_load_save_round_trip(tmp_path):
    p = tmp_path / "wiki.html"
    p.write_text(_make_html([{"title": "T", "text": "before"}]), encoding="utf-8")
    html, tiddlers, start, end = _load(str(p))
    tiddlers[0]["text"] = "after"
    _save(html, tiddlers, start, end, str(p))
    _, tiddlers2, _, _ = _load(str(p))
    assert tiddlers2[0]["text"] == "after"


def test_save_escapes_script_close_tag(tmp_path):
    p = tmp_path / "wiki.html"
    p.write_text(_make_html([{"title": "T", "text": "safe"}]), encoding="utf-8")
    html, tiddlers, start, end = _load(str(p))
    tiddlers[0]["text"] = "</script>"
    _save(html, tiddlers, start, end, str(p))
    raw = p.read_text(encoding="utf-8")
    store_section = raw.split(STORE_OPEN)[1].split(STORE_CLOSE)[0]
    assert "</script>" not in store_section


def test_load_raises_on_missing_store_open(tmp_path):
    p = tmp_path / "broken.html"
    p.write_text("<html>no store here</html>", encoding="utf-8")
    with pytest.raises(ValueError):
        _load(str(p))


def test_load_raises_on_invalid_json(tmp_path):
    p = tmp_path / "broken.html"
    p.write_text(f"<html>{STORE_OPEN}not valid json{STORE_CLOSE}</html>", encoding="utf-8")
    with pytest.raises(Exception):
        _load(str(p))


# ---------------------------------------------------------------------------
# UUID keys
# ---------------------------------------------------------------------------

def test_todolist_keys_are_uuids():
    tiddlers = []
    add_todolist(tiddlers, "High", ["Task A", "Task B"])
    tasks = json.loads(_find(tiddlers, "$:/todolist/data/tasks/High")["text"])
    for key in tasks:
        parsed = uuid.UUID(key)  # raises if not a valid UUID
        assert str(parsed) == key


def test_todolist_merge_new_keys_are_uuids():
    tiddlers = []
    add_todolist(tiddlers, "High", ["Task A"])
    add_todolist(tiddlers, "High", ["Task A", "Task B"])
    tasks = json.loads(_find(tiddlers, "$:/todolist/data/tasks/High")["text"])
    for key in tasks:
        uuid.UUID(key)  # raises if not a valid UUID


# ---------------------------------------------------------------------------
# done / state tiddlers after merge
# ---------------------------------------------------------------------------

def test_add_todolist_merge_done_tiddler_unchanged():
    tiddlers = []
    add_todolist(tiddlers, "High", ["Task A"])
    # Simulate user marking a task done
    done_t = _find(tiddlers, "$:/todolist/data/done/High")
    done_t["text"] = json.dumps({"some-key": "Task A"})
    add_todolist(tiddlers, "High", ["Task A", "Task B"])
    done_after = json.loads(_find(tiddlers, "$:/todolist/data/done/High")["text"])
    assert "some-key" in done_after  # user's done entry preserved


def test_add_todolist_merge_state_tiddler_unchanged():
    tiddlers = []
    add_todolist(tiddlers, "High", ["Task A"])
    state_t = _find(tiddlers, "$:/todolist/data/state/High")
    state_t["text"] = json.dumps({"itemtext": "draft text", "markall": ""})
    add_todolist(tiddlers, "High", ["Task A", "Task B"])
    state_after = json.loads(_find(tiddlers, "$:/todolist/data/state/High")["text"])
    assert state_after["itemtext"] == "draft text"


# ---------------------------------------------------------------------------
# add_or_update — tiddler_type edge cases
# ---------------------------------------------------------------------------

def test_add_or_update_tiddler_type_set_on_create():
    tiddlers = []
    add_or_update(tiddlers, "T", "text", tiddler_type="application/json")
    assert tiddlers[0]["type"] == "application/json"


def test_add_or_update_tiddler_type_none_preserves_existing():
    tiddlers = []
    add_or_update(tiddlers, "T", "text", tiddler_type="application/json")
    add_or_update(tiddlers, "T", "updated", tiddler_type=None)
    assert tiddlers[0]["type"] == "application/json"


# ---------------------------------------------------------------------------
# add_or_update — empty string tags
# ---------------------------------------------------------------------------

def test_add_or_update_empty_string_tags_not_stored_on_create():
    tiddlers = []
    add_or_update(tiddlers, "T", "text", tags="")
    assert "tags" not in tiddlers[0]
