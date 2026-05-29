from pathlib import Path


def test_agents_dir_has_no_business_heuristics():
    agents = Path(__file__).resolve().parents[1] / "app" / "agents"
    text = "\n".join(f.read_text(encoding="utf-8") for f in agents.glob("*.py"))
    forbidden = ["RISK_KEYWORDS", "_heuristic", "diagram_from_modules", "project_detect"]
    for token in forbidden:
        assert token not in text, f"发现禁止的业务硬编码: {token}"
