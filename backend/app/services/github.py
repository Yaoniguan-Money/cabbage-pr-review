from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

import httpx

from app.config import settings

PR_URL_PATTERN = re.compile(
    r"https?://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/(?P<number>\d+)",
    re.I,
)


def parse_pr_url(url: str) -> tuple[str, str, int]:
    m = PR_URL_PATTERN.search(url.strip())
    if not m:
        raise ValueError("无效的 GitHub PR URL，示例：https://github.com/owner/repo/pull/123")
    return m.group("owner"), m.group("repo"), int(m.group("number"))


class GitHubService:
    def __init__(self) -> None:
        headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        if settings.github_token:
            headers["Authorization"] = f"Bearer {settings.github_token}"
        self._headers = headers

    async def fetch_pr_context(self, pr_url: str) -> dict[str, Any]:
        owner, repo, number = parse_pr_url(pr_url)
        base = f"https://api.github.com/repos/{owner}/{repo}"
        async with httpx.AsyncClient(timeout=60.0, headers=self._headers) as client:
            pr_resp = await client.get(f"{base}/pulls/{number}")
            pr_resp.raise_for_status()
            pr = pr_resp.json()
            files_resp = await client.get(f"{base}/pulls/{number}/files", params={"per_page": 100})
            files_resp.raise_for_status()
            files = files_resp.json()
        patches: list[dict[str, Any]] = []
        file_paths: list[str] = []
        for f in files:
            file_paths.append(f.get("filename", ""))
            patches.append(
                {
                    "filename": f.get("filename"),
                    "status": f.get("status"),
                    "patch": f.get("patch") or "",
                    "additions": f.get("additions", 0),
                    "deletions": f.get("deletions", 0),
                }
            )
        return {
            "owner": owner,
            "repo": repo,
            "number": number,
            "title": pr.get("title", ""),
            "body": pr.get("body") or "",
            "base_sha": pr["base"]["sha"],
            "head_sha": pr["head"]["sha"],
            "base_ref": pr["base"]["ref"],
            "head_ref": pr["head"]["ref"],
            "html_url": pr.get("html_url", pr_url),
            "file_paths": file_paths,
            "patches": patches,
            "changed_files_count": len(files),
        }

    @staticmethod
    def is_valid_pr_url(url: str) -> bool:
        return bool(PR_URL_PATTERN.search(url.strip()))


github_service = GitHubService()
