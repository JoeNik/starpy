from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    APP_ENV: str = "production"
    APP_DEBUG: bool = False
    APP_NAME: str = "Star Savings"
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./storage/app/database.sqlite"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:8008"
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 2097152  # 2MB
    ALLOWED_IMAGE_TYPES: str = "image/jpeg,image/png,image/gif,image/webp"
    
    # Storage
    STORAGE_PATH: str = "./storage"
    UPLOAD_DIR: str = "./storage"  # 文件上传根目录
    API_URL: str = "http://localhost:8000"  # API 根地址
    AVATARS_PATH: str = "storage/avatars"
    REWARDS_PATH: str = "storage/rewards"
    
    # 日志配置
    LOG_LEVEL: str = Field(default="INFO", description="日志级别: DEBUG, INFO, WARNING, ERROR, CRITICAL")
    LOG_DIR: str = Field(default="./storage/logs", description="日志文件目录")
    LOG_FILE: str = Field(default="app.log", description="应用日志文件名")
    LOG_MAX_BYTES: int = Field(default=10485760, description="单个日志文件最大大小(字节),默认10MB")
    LOG_BACKUP_COUNT: int = Field(default=5, description="保留的日志文件数量")
    
    # 钱包配置
    SAVINGS_BOX_ANNUAL_INTEREST_RATE: float = Field(
        default=5.0,
        description="存钱罐年化利率（百分比），默认5%"
    )
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True
    )
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert CORS_ORIGINS string to list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    @property
    def allowed_image_types_list(self) -> List[str]:
        """Convert ALLOWED_IMAGE_TYPES string to list."""
        return [mime.strip() for mime in self.ALLOWED_IMAGE_TYPES.split(",")]


settings = Settings()