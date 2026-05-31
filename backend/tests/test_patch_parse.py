from app.local.file_io import parse_patch_text


def test_parse_patch_text():
    patch = """diff --git a/foo.py b/foo.py
--- a/foo.py
+++ b/foo.py
@@ -1 +1 @@
+x = 1
"""
    files = parse_patch_text(patch)
    assert len(files) >= 1
    assert files[0]["filename"] == "foo.py"
    assert files[0]["additions"] == 1
    assert files[0]["deletions"] == 0


def test_parse_patch_text_counts_multi_line():
    from app.local.demo_patches_meta import list_demo_patches

    s2 = next(s for s in list_demo_patches()["scenarios"] if s["id"] == "S2-change-surface")
    files = parse_patch_text(s2["patch_text"])
    assert len(files) >= 8
    docker = next(f for f in files if f["filename"] == "Dockerfile")
    assert docker["additions"] > 0 or docker["deletions"] > 0
