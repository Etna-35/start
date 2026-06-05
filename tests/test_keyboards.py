from app.services.keyboards import parse_callback, score_keyboard, start_keyboard


def test_score_keyboard_structure():
    kb = score_keyboard("E1")
    assert isinstance(kb, list) and len(kb) == 1
    att = kb[0]
    assert att["type"] == "inline_keyboard"
    rows = att["payload"]["buttons"]
    assert len(rows) == 3
    # First row: A/B/C/D
    first = rows[0]
    assert [b["text"] for b in first] == ["A", "B", "C", "D"]
    assert all(b["type"] == "callback" for b in first)
    assert first[0]["payload"] == "rv|s|E1|A"
    assert first[3]["payload"] == "rv|s|E1|D"
    # Bulk row payloads
    bulk = rows[2]
    assert [b["payload"] for b in bulk] == ["rv|b|B", "rv|b|C", "rv|b|D"]


def test_start_keyboard_structure():
    kb = start_keyboard()
    button = kb[0]["payload"]["buttons"][0][0]
    assert button["type"] == "callback"
    assert button["payload"] == "rv|start"


def test_parse_callback():
    assert parse_callback("rv|s|abc-123|A") == ["rv", "s", "abc-123", "A"]
    assert parse_callback("rv|k|abc-123") == ["rv", "k", "abc-123"]
    assert parse_callback("rv|b|B") == ["rv", "b", "B"]
    assert parse_callback("rv|start") == ["rv", "start"]
    assert parse_callback("rv|done") == ["rv", "done"]
    assert parse_callback("tm|22:00") == ["tm", "22:00"]


def test_parse_callback_rejects_foreign():
    assert parse_callback("foo|x") is None
    assert parse_callback("") is None
    assert parse_callback("rv") is None
