from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_detail_page_meta_api():
    resp = client.get("/api/detail-page-meta")
    assert resp.status_code == 200
    body = resp.json()
    ui = body["ui_strings"]
    assert ui["nav_files"]
    assert ui["diff_empty"]
    assert ui["status_running"]
    assert ui["task_id_toggle_show"]
    assert ui["agent_stepper_label"]
    assert ui["agent_parallel_lane_aria"]
    assert ui["parallel_running_hint"]
    assert "{ref}" in ui["branch_into"]
    assert "{task_id}" in ui["export_filename_template"]
    assert ui["export_disabled_hint"]
    assert ui["export_meta_missing"]
    assert ui["export_loading"]
    assert body["export_blob_revoke_delay_ms"] > 0
