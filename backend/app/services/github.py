from __future__ import annotations

import base64
import re
from typing import Any

import httpx

from app.config import settings
from app.local.cache import cache_get, cache_set

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

    async def _get_readme(self, client: httpx.AsyncClient, base: str) -> str:
        cache_key = f"readme:{base}"
        cached = cache_get(cache_key)
        if cached is not None:
            return cached
        try:
            resp = await client.get(f"{base}/readme")
            if resp.status_code != 200:
                return ""
            data = resp.json()
            content = base64.b64decode(data.get("content", "")).decode("utf-8", errors="ignore")
            cache_set(cache_key, content)
            return content
        except Exception:
            return ""

    async def _get_tree_paths(self, client: httpx.AsyncClient, base: str, sha: str) -> list[str]:
        cache_key = f"tree:{base}:{sha}"
        cached = cache_get(cache_key)
        if cached is not None:
            return cached
        try:
            resp = await client.get(f"{base}/git/trees/{sha}", params={"recursive": "1"})
            if resp.status_code != 200:
                return []
            data = resp.json()
            paths = [
                item["path"]
                for item in data.get("tree", [])
                if item.get("type") == "blob" and not item["path"].startswith(".git")
            ][:500]
            cache_set(cache_key, paths)
            return paths
        except Exception:
            return []

    async def fetch_pr_context(self, pr_url: str) -> dict[str, Any]:
        owner, repo, number = parse_pr_url(pr_url)
        base_url = f"https://api.github.com/repos/{owner}/{repo}"
        async with httpx.AsyncClient(timeout=60.0, headers=self._headers) as client:
            pr_resp = await client.get(f"{base_url}/pulls/{number}")
            pr_resp.raise_for_status()
            pr = pr_resp.json()
            files_resp = await client.get(f"{base_url}/pulls/{number}/files", params={"per_page": 100})
            files_resp.raise_for_status()
            files = files_resp.json()
            readme = await self._get_readme(client, base_url)
            base_sha = pr["base"]["sha"]
            head_sha = pr["head"]["sha"]
            base_tree = await self._get_tree_paths(client, base_url, base_sha)
            head_tree = await self._get_tree_paths(client, base_url, head_sha)

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
            "base_sha": base_sha,
            "head_sha": head_sha,
            "base_ref": pr["base"]["ref"],
            "head_ref": pr["head"]["ref"],
            "html_url": pr.get("html_url", pr_url),
            "file_paths": file_paths,
            "patches": patches,
            "changed_files_count": len(files),
            "readme": readme,
            "base_tree": base_tree,
            "head_tree": head_tree,
            "tree": head_tree,
            "input_type": "pr_url",
        }

    @staticmethod
    def is_valid_pr_url(url: str) -> bool:
        return bool(PR_URL_PATTERN.search(url.strip()))


github_service = GitHubService()
