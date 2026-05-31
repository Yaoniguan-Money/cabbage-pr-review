"""用户领域模型。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class UserRecord:
    id: int
    username: str
    role: str = "user"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role,
        }

    def is_admin(self) -> bool:
        return self.role == "administrator"
