from __future__ import annotations

from typing import Any


def detect_project(file_paths: list[str], patches: list[dict] | None = None) -> tuple[str, str]:
    paths = " ".join(file_paths).lower()
    patch_text = ""
    if patches:
        patch_text = " ".join(p.get("patch", "") or "" for p in patches).lower()
    combined = paths + " " + patch_text
    project_type = "unknown"
    framework = "unknown"
    if "fastapi" in combined or "from fastapi" in combined:
        framework = "FastAPI"
        project_type = "python-api"
    elif "express" in combined or "require('express')" in combined:
        framework = "Express"
        project_type = "node-api"
    elif any(x in combined for x in ("react", "vite", "tsx", "jsx")):
        framework = "React/Vite"
        project_type = "frontend"
    elif any(p.endswith(".py") for p in file_paths):
        project_type = "python"
        framework = framework if framework != "unknown" else "Python"
    elif any(p.endswith((".ts", ".tsx", ".js", ".jsx")) for p in file_paths):
        project_type = "typescript"
        framework = framework if framework != "unknown" else "TypeScript/JavaScript"
    return project_type, framework
