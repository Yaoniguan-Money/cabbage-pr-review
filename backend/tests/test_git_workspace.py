import subprocess
from pathlib import Path

from app.services.git_workspace import GitWorkspace, _github_repo_url, redact_git_secrets


def test_github_repo_url_with_token():
    url = _github_repo_url("octo", "repo", "ghp_secret_token_12345")
    assert url == "https://x-access-token:ghp_secret_token_12345@github.com/octo/repo.git"


def test_redact_git_secrets():
    raw = "failed with ghp_abc123xyz and bearer ghp_abc123xyz"
    assert "ghp_abc123xyz" not in redact_git_secrets(raw, "ghp_abc123xyz")
    assert "ghp_***" in redact_git_secrets(raw)


def test_git_show_file(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    f = repo / "hello.txt"
    f.write_text("line1\n", encoding="utf-8")
    subprocess.run(["git", "add", "hello.txt"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo, check=True, capture_output=True)
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()
    ws = GitWorkspace(root=repo, base_sha=head, head_sha=head, ephemeral=False)
    content = ws.read_files_at_ref(["hello.txt"], head)
    assert "line1" in content.get("hello.txt", "")
