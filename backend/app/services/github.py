from __future__ import annotations

import base64
import logging
import re
from typing import Any

import httpx

from app.llm.credentials_resolve import resolve_github_token
from app.local.cache import cache_get, cache_set

logger = logging.getLogger(__name__)

PR_URL_PATTERN = re.compile(
    r"https?://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/(?P<number>\d+)",
    re.I,
)

MAX_PR_FILES = 300
FILES_PER_PAGE = 100


def parse_pr_url(url: str) -> tuple[str, str, int]:
    m = PR_URL_PATTERN.search(url.strip())
    if not m:
        raise ValueError("无效的 GitHub PR URL，示例：https://github.com/owner/repo/pull/123")
    return m.group("owner"), m.group("repo"), int(m.group("number"))


class GitHubService:
    def _headers_for_token(self, token: str | None = None) -> dict[str, str]:
        headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        # token 为任务级已解析的字符串；仅无 token 时回退服务器 .env
        tok = (token or "").strip() or resolve_github_token(None)
        if tok:
            headers["Authorization"] = f"Bearer {tok}"
        return headers

    async def _get_readme(
        self,
        client: httpx.AsyncClient,
        base: str,
        warnings: list[str],
    ) -> str:
        cache_key = f"readme:{base}"
        cached = cache_get(cache_key)
        if cached is not None:
            return cached
        try:
            resp = await client.get(f"{base}/readme")
            if resp.status_code != 200:
                warnings.append(f"README 获取 HTTP {resp.status_code}")
                return ""
            data = resp.json()
            content = base64.b64decode(data.get("content", "")).decode("utf-8", errors="ignore")
            cache_set(cache_key, content)
            return content
        except Exception as exc:
            logger.warning("Failed to fetch README for %s: %s", base, exc)
            warnings.append(f"README 获取失败: {exc}")
            return ""

    async def _get_tree_paths(
        self,
        client: httpx.AsyncClient,
        base: str,
        sha: str,
        warnings: list[str],
    ) -> list[str]:
        cache_key = f"tree:{base}:{sha}"
        cached = cache_get(cache_key)
        if cached is not None:
            return cached
        try:
            resp = await client.get(f"{base}/git/trees/{sha}", params={"recursive": "1"})
            if resp.status_code != 200:
                warnings.append(f"目录树获取 HTTP {resp.status_code}（{sha[:8]}）")
                return []
            data = resp.json()
            paths = [
                item["path"]
                for item in data.get("tree", [])
                if item.get("type") == "blob" and not item["path"].startswith(".git")
            ][:500]
            cache_set(cache_key, paths)
            return paths
        except Exception as exc:
            logger.warning("Failed to fetch tree for %s@%s: %s", base, sha, exc)
            warnings.append(f"目录树获取失败: {exc}")
            return []

    async def _fetch_pr_files(
        self,
        client: httpx.AsyncClient,
        base_url: str,
        number: int,
        warnings: list[str],
    ) -> list[dict[str, Any]]:
        files: list[dict[str, Any]] = []
        page = 1
        while len(files) < MAX_PR_FILES:
            resp = await client.get(
                f"{base_url}/pulls/{number}/files",
                params={"per_page": FILES_PER_PAGE, "page": page},
            )
            resp.raise_for_status()
            batch = resp.json()
            if not batch:
                break
            files.extend(batch)
            if len(batch) < FILES_PER_PAGE:
                break
            page += 1
        if len(files) > MAX_PR_FILES:
            warnings.append(f"PR 变更文件超过 {MAX_PR_FILES} 条，已截断至前 {MAX_PR_FILES} 条")
            files = files[:MAX_PR_FILES]
        return files

    async def fetch_pr_context(self, pr_url: str, *, github_token: str | None = None) -> dict[str, Any]:
        owner, repo, number = parse_pr_url(pr_url)
        base_url = f"https://api.github.com/repos/{owner}/{repo}"
        headers = self._headers_for_token(github_token)
        fetch_warnings: list[str] = []
        async with httpx.AsyncClient(timeout=60.0, headers=headers) as client:
            pr_resp = await client.get(f"{base_url}/pulls/{number}")
            pr_resp.raise_for_status()
            pr = pr_resp.json()
            files = await self._fetch_pr_files(client, base_url, number, fetch_warnings)
            readme = await self._get_readme(client, base_url, fetch_warnings)
            base_sha = pr["base"]["sha"]
            head_sha = pr["head"]["sha"]
            base_tree = await self._get_tree_paths(client, base_url, base_sha, fetch_warnings)
            head_tree = await self._get_tree_paths(client, base_url, head_sha, fetch_warnings)

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
        ctx: dict[str, Any] = {
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
        if fetch_warnings:
            ctx["fetch_warnings"] = fetch_warnings
        return ctx

    @staticmethod
    def is_valid_pr_url(url: str) -> bool:
        return bool(PR_URL_PATTERN.search(url.strip()))


github_service = GitHubService()
