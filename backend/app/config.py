from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# 仓库根目录 pr/（config 位于 backend/app/config.py）
REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_FILES = (
    Path(".env"),
    REPO_ROOT / ".env",
    Path(__file__).resolve().parents[1] / ".env",  # backend/.env
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=[str(p) for p in ENV_FILES if p.exists()] or ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    # v2.0 §7.3：Flash 轻任务 / Pro 重任务（API 模型名以 DeepSeek 控制台为准）
    deepseek_flash_model: str = "deepseek-chat"
    deepseek_pro_model: str = "deepseek-reasoner"
    github_token: str = ""
    use_mock_llm: bool = False

    @property
    def llm_enabled(self) -> bool:
        return bool(self.deepseek_api_key.strip())


settings = Settings()
