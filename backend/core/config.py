"""Configuration management for the integration hub."""

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # API Configuration
    api_secret_key: str = Field(default="change-me-in-production", env="API_SECRET_KEY")
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    
    # WebSocket Configuration
    websocket_enabled: bool = Field(default=True, env="WEBSOCKET_ENABLED")
    websocket_port: int = Field(default=8001, env="WEBSOCKET_PORT")
    
    # Database Configuration
    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/integration_hub.db",
        env="DATABASE_URL"
    )
    
    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    
    # Gemini Configuration
    GEMINI_API_KEY: Optional[str] = Field(default=None, env="GEMINI_API_KEY")
    GEMINI_MODEL: str = Field(default="gemini-3-flash-preview", env="GEMINI_MODEL")
    
    # Slack Configuration
    slack_bot_token: Optional[str] = Field(default=None, env="SLACK_BOT_TOKEN")
    slack_signing_secret: Optional[str] = Field(default=None, env="SLACK_SIGNING_SECRET")
    
    # Discord Configuration
    discord_bot_token: Optional[str] = Field(default=None, env="DISCORD_BOT_TOKEN")
    discord_client_id: Optional[str] = Field(default=None, env="DISCORD_CLIENT_ID")
    discord_client_secret: Optional[str] = Field(default=None, env="DISCORD_CLIENT_SECRET")
    
    # Email Configuration
    smtp_host: Optional[str] = Field(default=None, env="SMTP_HOST")
    smtp_port: int = Field(default=587, env="SMTP_PORT")
    smtp_user: Optional[str] = Field(default=None, env="SMTP_USER")
    smtp_password: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    smtp_from_email: Optional[str] = Field(default=None, env="SMTP_FROM_EMAIL")
    
    # Webhook Configuration
    webhook_secret: str = Field(default="change-me", env="WEBHOOK_SECRET")
    webhook_base_url: str = Field(default="http://localhost:8000", env="WEBHOOK_BASE_URL")
    
    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    rate_limit_requests_per_minute: int = Field(
        default=60,
        env="RATE_LIMIT_REQUESTS_PER_MINUTE"
    )
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


