"""Capture a secret-free environment snapshot for the evidence package."""

from __future__ import annotations

import importlib.metadata
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "evidence" / "environment.json"


def _command_version(command: list[str]) -> str | None:
    try:
        return subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None


def _package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def main() -> None:
    packages = {
        name: _package_version(name)
        for name in (
            "coverage",
            "fastapi",
            "httpx",
            "polars",
            "pydantic",
            "pytest",
            "requests",
        )
    }
    payload = {
        "schema_version": 1,
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python": sys.version,
        "python_executable": sys.executable,
        "node": _command_version(["node", "--version"]),
        "npm": _command_version(["npm.cmd" if os.name == "nt" else "npm", "--version"]),
        "python_packages": packages,
        "provider_credentials_present": {
            "DASHSCOPE_API_KEY": bool(os.environ.get("DASHSCOPE_API_KEY", "").strip()),
            "DEEPSEEK_API_KEY": bool(os.environ.get("DEEPSEEK_API_KEY", "").strip()),
        },
        "secret_values_recorded": False,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
