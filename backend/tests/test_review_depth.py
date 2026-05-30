from fastapi.testclient import TestClient

from app.local.review_depth import (
    get_review_depth_profile,
    list_review_depth_options,
    normalize_review_depth_mode,
)
from app.main import app

client = TestClient(app)

_DEPTH_OPTION_KEYS = frozenset(
    {
        "id",
        "label",
        "summary",
        "detail_bullets",
        "estimated_time",
        "cost_tier",
        "cost_tier_label",
        "default",
    }
)


def test_normalize_review_depth_mode():
    assert normalize_review_depth_mode("aggressive") == "aggressive"
    assert normalize_review_depth_mode("invalid", "balanced") == "balanced"


def test_profiles_differ_by_batch_limits():
    c = get_review_depth_profile("conservative")
    b = get_review_depth_profile("balanced")
    a = get_review_depth_profile("aggressive")
    assert c.atoms_per_batch < b.atoms_per_batch or c.max_batches_per_depth < b.max_batches_per_depth
    assert a.max_batches_per_depth > b.max_batches_per_depth
    assert c.gap_fill_pro_calls_per_batch == 0
    assert b.gap_fill_pro_calls_per_batch == 1


def test_list_options_from_single_source():
    opts = list_review_depth_options("balanced")
    assert len(opts) == 3
    labels = {o["label"] for o in opts}
    assert "快速审阅" in labels
    assert "标准审阅" in labels
    assert "深度审阅" in labels
    assert sum(1 for o in opts if o["default"]) == 1
    for o in opts:
        assert _DEPTH_OPTION_KEYS <= set(o.keys())
        assert o["summary"]
        assert o["detail_bullets"]
        assert o["cost_tier"] in {"low", "medium", "high"}
        assert o["cost_tier_label"].startswith("Token：")


def test_review_depth_options_api_contract():
    resp = client.get("/api/review-depth-options")
    assert resp.status_code == 200
    body = resp.json()
    assert "options" in body
    assert len(body["options"]) == 3
    for opt in body["options"]:
        assert _DEPTH_OPTION_KEYS <= set(opt.keys())
