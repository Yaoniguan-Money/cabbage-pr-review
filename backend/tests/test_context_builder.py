from app.local.context_builder import build_version_scan_context, load_extra_context_files


def test_version_context_split():
    ctx = {
        "patches": [
            {"filename": "a.py", "status": "removed", "patch": "-x=1"},
            {"filename": "b.py", "status": "added", "patch": "+y=2"},
        ],
        "file_paths": ["a.py", "b.py"],
        "readme": "readme text",
    }
    base = build_version_scan_context(ctx, version="base")
    head = build_version_scan_context(ctx, version="head")
    assert "a.py" in base["file_paths"] or base["file_paths"]
    assert "b.py" in head["file_paths"] or head["file_paths"]
    assert base["version"] == "base"
    assert head["version"] == "head"


def test_load_extra_context_empty():
    assert load_extra_context_files({}, []) == {}
