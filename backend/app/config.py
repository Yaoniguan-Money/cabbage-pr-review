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
    # v2.0 §7.3：Flash 轻任务 / Pro 重任务（API 模型名以控制台为准）
    deepseek_flash_model: str = "deepseek-chat"
    deepseek_pro_model: str = "deepseek-reasoner"
    github_token: str = ""
    use_mock_llm: bool = False
    review_depth_mode: str = "balanced"

    # v2.2：推理模式与 Provider 配置（模型名来自 env，业务代码不得写死）
    llm_mode: str = "cloud_only"
    cloud_api_base: str = ""
    cloud_api_key: str = ""
    cloud_flash_model: str = ""
    cloud_pro_model: str = ""
    local_llm_base_url: str = "http://localhost:11434"
    local_llm_default_model: str = ""
    local_llm_timeout_sec: int = 180
    local_compress_enabled: bool = True
    rules_pack_path: str = ""

    # public：公网部署，忽略服务器 Key，仅接受请求内 runtime_credentials
    deploy_mode: str = "local"
    allow_runtime_credentials: bool = True
    cloud_timeout_sec: float = 120.0
    # 本地单人开发可选 true；公网/评委环境务必 false（或由 DEPLOY_MODE=public 强制关闭）
    use_server_github_token: bool = True
    use_server_cloud_credentials: bool = True

    @property
    def effective_use_server_github_token(self) -> bool:
        if self.is_public_deploy:
            return False
        return self.use_server_github_token

    @property
    def effective_use_server_cloud_credentials(self) -> bool:
        if self.is_public_deploy:
            return False
        return self.use_server_cloud_credentials

    @property
    def cloud_api_base_resolved(self) -> str:
        return (self.cloud_api_base or self.deepseek_base_url).strip()

    @property
    def cloud_api_key_resolved(self) -> str:
        return (self.cloud_api_key or self.deepseek_api_key).strip()

    @property
    def cloud_flash_model_resolved(self) -> str:
        return (self.cloud_flash_model or self.deepseek_flash_model).strip()

    @property
    def cloud_pro_model_resolved(self) -> str:
        return (self.cloud_pro_model or self.deepseek_pro_model).strip()

    @property
    def llm_enabled(self) -> bool:
        from app.llm.credentials_resolve import server_cloud_configured

        return server_cloud_configured()

    @property
    def is_public_deploy(self) -> bool:
        return self.deploy_mode.strip().lower() == "public"


settings = Settings()
