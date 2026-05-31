from fastapi.testclient import TestClient

from app.local.export_meta import EXPORT_NOT_READY_DETAIL, format_export_filename
from app.main import app
from app.models.schemas import InputType, TaskRecord, TaskResultSchema
from app.services.task_store import task_store

client = TestClient(app)


def test_export_md_attachment_when_result_ready():
    record = TaskRecord(
        id="export-ready-1",
        input_type=InputType.PATCH,
        input_value="diff",
        result=TaskResultSchema(summary="ok", summary_bullets=[]),
    )
    task_store.update(record)
    resp = client.get(f"/api/tasks/{record.id}/export.md")
    assert resp.status_code == 200
    assert "attachment" in resp.headers.get("content-disposition", "").lower()
    assert format_export_filename(record.id) in resp.headers["content-disposition"]
    assert "# AI PR Review 报告" in resp.text


def test_export_md_409_when_no_result():
    record = TaskRecord(
        id="export-pending-1",
        input_type=InputType.PATCH,
        input_value="diff",
        result=None,
    )
    task_store.update(record)
    resp = client.get(f"/api/tasks/{record.id}/export.md")
    assert resp.status_code == 409
    assert resp.json()["detail"] == EXPORT_NOT_READY_DETAIL
