from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_flash_model: str = "deepseek-chat"
    deepseek_pro_model: str = "deepseek-chat"
    github_token: str = ""
    use_mock_llm: bool = True  # 无 API Key 时自动走启发式 Mock

    @property
    def llm_enabled(self) -> bool:
        return bool(self.deepseek_api_key.strip())


settings = Settings()
if settings.llm_enabled:
    settings.use_mock_llm = False
