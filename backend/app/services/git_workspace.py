from __future__ import annotations

import asyncio
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.config import settings
from app.local.text_preprocess import truncate

MAX_FILES = 40
MAX_BYTES = 50_000


@dataclass
class GitWorkspace:
    root: Path
    base_sha: str
    head_sha: str
    ephemeral: bool = False

    def read_files_at_ref(self, paths: list[str], ref: str) -> dict[str, str]:
        out: dict[str, str] = {}
        for rel in paths[:MAX_FILES]:
            rel = rel.replace("\\", "/")
            try:
                proc = subprocess.run(
                    ["git", "show", f"{ref}:{rel}"],
                    cwd=self.root,
                    capture_output=True,
                    text=True,
                    timeout=60,
                    check=True,
                )
                if proc.stdout:
                    out[rel] = truncate(proc.stdout, MAX_BYTES)
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
                continue
        return out

    def cleanup(self) -> None:
        if self.ephemeral:
            shutil.rmtree(self.root, ignore_errors=True)


def _git_cmd(*parts: str, token: str = "") -> list[str]:
    """构建 git 命令；凭据通过 extraHeader 传递，避免写入 clone URL。"""
    if token:
        header = f"http.https://github.com/.extraHeader=AUTHORIZATION: bearer {token}"
        return ["git", "-c", header, *parts]
    return ["git", *parts]


def _run_git(args: list[str], cwd: Path) -> None:
    proc = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=300)
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} 失败: {proc.stderr or proc.stdout}")


def _prepare_github_workspace(
    owner: str,
    repo: str,
    base_sha: str,
    head_sha: str,
    *,
    github_token: str = "",
) -> GitWorkspace:
    tmp = Path(tempfile.mkdtemp(prefix="pr-review-"))
    repo_dir = tmp / "repo"
    url = f"https://github.com/{owner}/{repo}.git"
    from app.llm.credentials_resolve import resolve_github_token

    token = (github_token or "").strip() or resolve_github_token(None)
    _run_git(
        _git_cmd("clone", "--filter=blob:none", url, str(repo_dir), token=token),
        cwd=tmp,
    )
    _run_git(
        _git_cmd("fetch", "origin", base_sha, head_sha, "--depth=1", token=token),
        cwd=repo_dir,
    )
    return GitWorkspace(root=repo_dir, base_sha=base_sha, head_sha=head_sha, ephemeral=True)


def _prepare_local_workspace(repo_path: Path) -> GitWorkspace:
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_path,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    base = subprocess.run(
        ["git", "rev-parse", "HEAD~1"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    base_sha = base.stdout.strip() if base.returncode == 0 else head
    return GitWorkspace(root=repo_path.resolve(), base_sha=base_sha, head_sha=head, ephemeral=False)


async def enrich_context_with_git(
    ctx: dict[str, Any],
    *,
    github_token: str = "",
) -> tuple[dict[str, Any], GitWorkspace | None]:
    """填充 base_file_contents / head_file_contents；返回可能需任务结束后 cleanup 的工作区。"""
    paths = list(ctx.get("file_paths", []))
    if not paths:
        return ctx, None

    ws: GitWorkspace | None = None
    if ctx.get("owner") and ctx.get("repo") and ctx.get("base_sha") and ctx.get("head_sha"):
        ws = await asyncio.to_thread(
            _prepare_github_workspace,
            ctx["owner"],
            ctx["repo"],
            ctx["base_sha"],
            ctx["head_sha"],
            github_token=github_token,
        )
    elif ctx.get("local_root"):
        root = Path(ctx["local_root"])
        if (root / ".git").exists():
            ws = await asyncio.to_thread(_prepare_local_workspace, root)

    if ws:
        ctx["base_file_contents"] = await asyncio.to_thread(ws.read_files_at_ref, paths, ws.base_sha)
        ctx["head_file_contents"] = await asyncio.to_thread(ws.read_files_at_ref, paths, ws.head_sha)
        ctx["git_workspace_attached"] = True
    return ctx, ws
