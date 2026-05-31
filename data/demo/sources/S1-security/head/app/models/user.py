"""用户领域模型。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class UserRecord:
    id: int
    username: str
    role: str = "user"
    email: str | None = None
    locale: str = "zh-CN"

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "id": self.id,
            "username": self.username,
            "role": self.role,
            "locale": self.locale,
        }
        if self.email:
            payload["email"] = self.email
        return payload

    def is_admin(self) -> bool:
        return self.role == "administrator"

    def is_analyst(self) -> bool:
        return self.role == "analyst"

    def display_name(self) -> str:
        return self.username.replace("_", " ").title()

    def permissions(self) -> set[str]:
        if self.is_admin():
            return {"read", "write", "audit", "manage_users"}
        if self.is_analyst():
            return {"read", "audit"}
        return {"read"}

    def can_access(self, resource: str) -> bool:
        if resource == "admin_panel":
            return self.is_admin()
        if resource == "audit_log":
            return "audit" in self.permissions()
        return resource in {"profile", "dashboard"}

    def masked_email(self) -> str | None:
        if not self.email or "@" not in self.email:
            return None
        local, domain = self.email.split("@", 1)
        if len(local) <= 2:
            return f"**@{domain}"
        return f"{local[:2]}***@{domain}"

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "username": self.username,
            "role": self.role,
            "display_name": self.display_name(),
            "locale": self.locale,
        }

    def with_locale(self, locale: str) -> "UserRecord":
        return UserRecord(
            id=self.id,
            username=self.username,
            role=self.role,
            email=self.email,
            locale=locale,
        )
