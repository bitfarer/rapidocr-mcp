from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="RAPIDOCR_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Model paths
    det_model_path: str | None = None
    rec_model_path: str | None = None
    cls_model_path: str | None = None
    use_angle_cls: bool = True
    lang: str = "ch"
    model_dir: str = Field(default="~/.rapidocr_models")

    # OCR options
    confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    text_postprocessing_merge: bool = True
    text_postprocessing_deduplicate: bool = True

    # Output format
    default_output_format: Literal["plain", "json", "markdown", "structured"] = "json"

    # Image security
    max_image_size: int = Field(default=10 * 1024 * 1024, ge=1024)  # 10MB
    allowed_image_formats: list[str] = ["jpg", "jpeg", "png", "bmp", "webp", "tiff", "gif"]
    enable_path_whitelist: bool = False
    allowed_paths: list[str] = []

    # URL download
    url_cache_dir: str = Field(default="~/.rapidocr_cache")
    url_cache_ttl: int = Field(default=3600, ge=0)  # seconds

    # Rate limiting
    enable_rate_limit: bool = False
    rate_limit_requests: int = Field(default=100, ge=1)
    rate_limit_period: int = Field(default=60, ge=1)  # seconds
    max_concurrent_requests: int = Field(default=10, ge=1)

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_json: bool = False
    log_file: str | None = None

    # Server
    server_host: str = "0.0.0.0"
    server_port: int = 8080
    server_workers: int = 1

    # Security
    api_key: str | None = None
    enable_cors: bool = True
    cors_origins: list[str] = ["*"]
    enable_audit_log: bool = False

    # Monitoring
    enable_metrics: bool = True
    metrics_port: int = 9090

    # Hot reload config
    enable_config_reload: bool = False

    def resolve_path(self, path: str | None) -> str | None:
        if path is None:
            return None
        return str(Path(path).expanduser().resolve())

    @property
    def resolved_model_dir(self) -> str:
        return str(Path(self.model_dir).expanduser().resolve())

    @property
    def resolved_cache_dir(self) -> str:
        return str(Path(self.url_cache_dir).expanduser().resolve())

    def is_path_allowed(self, path: str) -> bool:
        if not self.enable_path_whitelist:
            return True
        resolved = Path(path).resolve()
        return any(str(resolved).startswith(allowed) for allowed in self.allowed_paths)


settings = Settings()
