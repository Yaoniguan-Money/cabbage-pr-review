import pytest

from app.services.github import GitHubService, parse_pr_url


def test_parse_pr_url():
    owner, repo, num = parse_pr_url("https://github.com/octocat/Hello-World/pull/1347")
    assert owner == "octocat"
    assert repo == "Hello-World"
    assert num == 1347


def test_invalid_pr_url():
    with pytest.raises(ValueError):
        parse_pr_url("https://example.com/not-a-pr")


def test_is_valid():
    assert GitHubService.is_valid_pr_url("https://github.com/a/b/pull/1")
    assert not GitHubService.is_valid_pr_url("invalid")
