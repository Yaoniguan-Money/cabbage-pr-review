"""规则 lint 与加载诊断测试。"""

from __future__ import annotations

from app.rules.rule_loader import lint_rules, load_rule_pack_with_lint


def test_load_rule_pack_with_lint_returns_clean_pack():
    rules, config, issues = load_rule_pack_with_lint()
    assert len(rules) >= 10
    assert config.scope.max_atoms_per_run >= 50
    assert issues == []


def test_lint_catches_invalid_regex():
    from app.rules.rule_schema import RuleDefinition, RuleMatchClause, RuleMatchGroup

    rules = [
        RuleDefinition(
            id="bad-regex",
            message="无效正则",
            match=RuleMatchGroup(
                any=[RuleMatchClause(pattern_regex="(?P<unclosed")]
            ),
        )
    ]
    issues = lint_rules(rules)
    assert any("bad-regex" in issue for issue in issues)
