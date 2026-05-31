from app.local.export_meta import (
    EXPORT_BLOB_REVOKE_DELAY_MS,
    EXPORT_FILENAME_TEMPLATE,
    format_export_filename,
)


def test_format_export_filename_uses_template():
    task_id = "0117e257-da95-461e-8057-ba3f7218838b"
    name = format_export_filename(task_id)
    assert name == EXPORT_FILENAME_TEMPLATE.replace("{task_id}", task_id)
    assert task_id in name


def test_revoke_delay_is_positive():
    assert EXPORT_BLOB_REVOKE_DELAY_MS > 0
