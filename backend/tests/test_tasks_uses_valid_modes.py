from pathlib import Path


def test_tasks_route_uses_valid_modes_not_inline_set():
    path = Path(__file__).resolve().parents[1] / "app" / "api" / "routes" / "tasks.py"
    text = path.read_text(encoding="utf-8")
    assert "VALID_MODES" in text
    assert '"conservative"' not in text or "VALID_MODES" in text
    assert '{"conservative"' not in text
    assert '{"conservative", "balanced", "aggressive"}' not in text
