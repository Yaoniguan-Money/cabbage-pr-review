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
