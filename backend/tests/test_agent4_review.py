from app.agents.agent4_review import _dedupe_risks, _needs_gap_fill
from app.local.review_depth import get_review_depth_profile
from app.models.schemas import DiffAtom, RiskItem, RiskReviewSchema


def test_dedupe_risks_by_id():
    risks = [
        RiskItem(id="r1", title="A", file_paths=["a.py"]),
        RiskItem(id="r1", title="A dup", file_paths=["a.py"]),
    ]
    out = _dedupe_risks(risks)
    assert len(out) == 1


def test_needs_gap_fill_conservative_disabled():
    profile = get_review_depth_profile("conservative")
    review = RiskReviewSchema(risks=[])
    atoms = [DiffAtom(id="a1", file_path="x", change_type="modified")]
    assert _needs_gap_fill(review, atoms, profile) is False


def test_needs_gap_fill_balanced_when_few_risks():
    profile = get_review_depth_profile("balanced")
    review = RiskReviewSchema(risks=[])
    atoms = [
        DiffAtom(id="a1", file_path="x", change_type="modified"),
        DiffAtom(id="a2", file_path="y", change_type="modified"),
    ]
    assert _needs_gap_fill(review, atoms, profile) is True
