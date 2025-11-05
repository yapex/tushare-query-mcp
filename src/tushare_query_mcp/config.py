"""
配置管理模块

基于 Pydantic Settings 的配置管理，支持从环境变量加载配置。
包含完整的参数验证和默认值设置。
"""

import os
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置类"""

    # 必需配置
    tushare_token: str = Field(..., description="Tushare API Token")

    # API 服务器配置
    api_host: str = Field(default="0.0.0.0", description="API 服务器地址")
    api_port: int = Field(default=8000, ge=1, le=65535, description="API 服务器端口")

    # 缓存配置
    cache_dir: str = Field(default="./.cache", description="缓存目录")
    income_cache_ttl: int = Field(
        default=86400 * 7, ge=0, description="利润表缓存时间（秒）"
    )
    balance_cache_ttl: int = Field(
        default=86400 * 7, ge=0, description="资产负债表缓存时间（秒）"
    )
    cashflow_cache_ttl: int = Field(
        default=86400 * 7, ge=0, description="现金流量表缓存时间（秒）"
    )
    stock_cache_ttl: int = Field(
        default=86400 * 30, ge=0, description="股票信息缓存时间（秒）"
    )

    # API 调用配置
    api_timeout: int = Field(default=30, ge=1, le=300, description="API 超时时间（秒）")
    max_retries: int = Field(default=3, ge=0, le=10, description="最大重试次数")

    # 日志配置
    log_level: str = Field(default="INFO", description="日志级别")

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        """验证日志级别"""
        if v is None:
            return "INFO"
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v.upper()

    @field_validator("api_host")
    @classmethod
    def validate_api_host(cls, v):
        """验证 API 主机地址"""
        if v is None:
            return "0.0.0.0"
        if not v.strip():
            raise ValueError("api_host cannot be empty")
        return v.strip()

    @field_validator("cache_dir")
    @classmethod
    def validate_cache_dir(cls, v):
        """验证缓存目录"""
        if v is None:
            v = "./.cache"
        if not v.strip():
            raise ValueError("cache_dir cannot be empty")
        # 确保目录路径存在
        os.makedirs(v, exist_ok=True)
        return v.strip()

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
        # 环境变量前缀
        "env_prefix": "",
        # 字段别名（环境变量名）使用 Pydantic v2 的 Field alias
    }

    @field_validator("tushare_token", mode="before")
    @classmethod
    def get_tushare_token(cls, v, info):
        """从环境变量获取 TUSHARE_TOKEN"""
        return v or os.getenv("TUSHARE_TOKEN")

    @field_validator("api_host", mode="before")
    @classmethod
    def get_api_host(cls, v, info):
        """从环境变量获取 API_HOST"""
        return v or os.getenv("API_HOST", "0.0.0.0")

    @field_validator("api_port", mode="before")
    @classmethod
    def get_api_port(cls, v, info):
        """从环境变量获取 API_PORT"""
        if v is None:
            port = os.getenv("API_PORT", "8000")
            return int(port)
        return v

    @field_validator("cache_dir", mode="before")
    @classmethod
    def get_cache_dir(cls, v, info):
        """从环境变量获取 CACHE_DIR"""
        return v or os.getenv("CACHE_DIR", "./.cache")

    @field_validator("income_cache_ttl", mode="before")
    @classmethod
    def get_income_cache_ttl(cls, v, info):
        """从环境变量获取 INCOME_CACHE_TTL"""
        if v is None:
            ttl = os.getenv("INCOME_CACHE_TTL", "604800")  # 7天
            return int(ttl)
        return v

    @field_validator("balance_cache_ttl", mode="before")
    @classmethod
    def get_balance_cache_ttl(cls, v, info):
        """从环境变量获取 BALANCE_CACHE_TTL"""
        if v is None:
            ttl = os.getenv("BALANCE_CACHE_TTL", "604800")  # 7天
            return int(ttl)
        return v

    @field_validator("cashflow_cache_ttl", mode="before")
    @classmethod
    def get_cashflow_cache_ttl(cls, v, info):
        """从环境变量获取 CASHFLOW_CACHE_TTL"""
        if v is None:
            ttl = os.getenv("CASHFLOW_CACHE_TTL", "604800")  # 7天
            return int(ttl)
        return v

    @field_validator("stock_cache_ttl", mode="before")
    @classmethod
    def get_stock_cache_ttl(cls, v, info):
        """从环境变量获取 STOCK_CACHE_TTL"""
        if v is None:
            ttl = os.getenv("STOCK_CACHE_TTL", "2592000")  # 30天
            return int(ttl)
        return v

    @field_validator("api_timeout", mode="before")
    @classmethod
    def get_api_timeout(cls, v, info):
        """从环境变量获取 API_TIMEOUT"""
        if v is None:
            timeout = os.getenv("API_TIMEOUT", "30")
            return int(timeout)
        return v

    @field_validator("max_retries", mode="before")
    @classmethod
    def get_max_retries(cls, v, info):
        """从环境变量获取 MAX_RETRIES"""
        if v is None:
            retries = os.getenv("MAX_RETRIES", "3")
            return int(retries)
        return v

    @field_validator("log_level", mode="before")
    @classmethod
    def get_log_level(cls, v, info):
        """从环境变量获取 LOG_LEVEL"""
        return v or os.getenv("LOG_LEVEL", "INFO")


# 全局配置实例
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    获取全局配置实例（单例模式）

    Returns:
        Settings: 配置实例
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """
    重新加载配置（主要用于测试）

    Returns:
        Settings: 新的配置实例
    """
    global _settings
    _settings = Settings()
    return _settings


def validate_token(token: str) -> bool:
    """
    验证 Tushare Token 格式

    Args:
        token: Tushare API Token

    Returns:
        bool: Token 格式是否有效
    """
    # 只需要验证 token 是否存在且不为空
    return token is not None and bool(token.strip())


# 导出主要接口
__all__ = [
    "Settings",
    "get_settings",
    "reload_settings",
    "validate_token",
]
