import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.github import GitHubService, MAX_PR_FILES, parse_pr_url


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


def test_headers_public_deploy_ignores_server_token(monkeypatch):
    monkeypatch.setattr("app.config.settings.deploy_mode", "public")
    monkeypatch.setattr(
        "app.services.github.resolve_github_token",
        lambda _token: "",
    )
    headers = GitHubService()._headers_for_token(None)
    assert "Authorization" not in headers


def test_headers_with_resolved_token(monkeypatch):
    monkeypatch.setattr(
        "app.services.github.resolve_github_token",
        lambda token: (token or "").strip() or "ghp_resolved",
    )
    headers = GitHubService()._headers_for_token("ghp_task_token")
    assert headers.get("Authorization") == "Bearer ghp_task_token"


@pytest.mark.asyncio
async def test_fetch_pr_files_paginates():
    svc = GitHubService()
    warnings: list[str] = []
    page1 = [{"filename": f"f{i}.py"} for i in range(100)]
    page2 = [{"filename": "extra.py"}]

    mock_client = AsyncMock()
    mock_resp1 = MagicMock()
    mock_resp1.raise_for_status = MagicMock()
    mock_resp1.json.return_value = page1
    mock_resp2 = MagicMock()
    mock_resp2.raise_for_status = MagicMock()
    mock_resp2.json.return_value = page2
    mock_client.get = AsyncMock(side_effect=[mock_resp1, mock_resp2])

    files = await svc._fetch_pr_files(mock_client, "https://api.github.com/repos/o/r", 1, warnings)
    assert len(files) == 101
    assert mock_client.get.await_count == 2


@pytest.mark.asyncio
async def test_fetch_pr_files_truncates_at_max(monkeypatch):
    monkeypatch.setattr("app.services.github.MAX_PR_FILES", 50)
    svc = GitHubService()
    warnings: list[str] = []
    huge = [{"filename": f"f{i}.py"} for i in range(100)]

    mock_client = AsyncMock()
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = huge
    mock_client.get = AsyncMock(return_value=mock_resp)

    files = await svc._fetch_pr_files(mock_client, "https://api.github.com/repos/o/r", 1, warnings)
    assert len(files) == 50
    assert any("截断" in w for w in warnings)
