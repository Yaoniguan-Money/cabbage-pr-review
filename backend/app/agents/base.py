from __future__ import annotations

from typing import Any


def extract_modules_from_paths(file_paths: list[str]) -> list[str]:
    modules: set[str] = set()
    for fp in file_paths:
        parts = fp.replace("\\", "/").split("/")
        if len(parts) >= 2:
            modules.add(parts[0])
        elif parts:
            modules.add(parts[0].split(".")[0])
    return sorted(modules)[:20]


def extract_routes_from_patches(patches: list[dict]) -> list[str]:
    routes: set[str] = set()
    for p in patches:
        patch = p.get("patch") or ""
        for line in patch.splitlines():
            s = line.strip()
            if any(k in s for k in ('@app.get', '@app.post', '@router.', 'router.get', 'app.get(', 'app.post(')):
                routes.add(s[:120])
            if 'path:' in s.lower() or 'route' in s.lower():
                routes.add(s[:120])
    return sorted(routes)[:15]
