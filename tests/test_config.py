"""
配置管理测试用例
测试 Settings 类的配置加载、验证和默认值功能
"""

import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

# 导入待测试的模块
from tushare_query_mcp.config import (Settings, get_settings, reload_settings,
                                      validate_token)


class TestSettings:
    """测试 Settings 配置类"""

    def test_settings_load_token_from_env(self):
        """测试从环境变量加载 token"""
        # 准备测试环境变量
        test_token = "test_tushare_token_12345"

        with patch.dict(os.environ, {"TUSHARE_TOKEN": test_token}):
            settings = Settings()
            assert settings.tushare_token == test_token

    def test_settings_default_values(self):
        """测试默认配置值"""
        # 测试所有默认值是否正确设置
        expected_defaults = {
            "api_host": "0.0.0.0",
            "api_port": 8000,
            "cache_dir": "./.cache",
            "income_cache_ttl": 86400 * 7,  # 7天
            "balance_cache_ttl": 86400 * 7,
            "cashflow_cache_ttl": 86400 * 7,
            "stock_cache_ttl": 86400 * 30,  # 30天
            "api_timeout": 30,
            "max_retries": 3,
            "log_level": "INFO",
        }

        settings = Settings(tushare_token="dummy_token")
        for key, expected_value in expected_defaults.items():
            assert getattr(settings, key) == expected_value

    def test_settings_validation_token_required(self):
        """测试 token 是必需的"""
        # 当没有设置 TUSHARE_TOKEN 时应该抛出 ValidationError
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings()

            # 验证错误信息包含 token 相关内容
            assert "tushare_token" in str(exc_info.value)

    def test_settings_validation_port_range(self):
        """测试端口号范围验证"""
        # 测试有效端口号
        valid_ports = [80, 443, 8000, 8080, 3000]

        for port in valid_ports:
            with patch.dict(os.environ, {"TUSHARE_TOKEN": "dummy"}):
                settings = Settings(api_port=port)
                assert settings.api_port == port

        # 测试无效端口号
        invalid_ports = [-1, 0, 65536, 100000]

        for port in invalid_ports:
            with patch.dict(os.environ, {"TUSHARE_TOKEN": "dummy"}):
                with pytest.raises(ValidationError):
                    Settings(api_port=port)

    def test_settings_cache_ttl_validation(self):
        """测试缓存TTL验证"""
        # 测试正数TTL
        valid_ttls = [60, 3600, 86400, 86400 * 7]

        for ttl in valid_ttls:
            with patch.dict(os.environ, {"TUSHARE_TOKEN": "dummy"}):
                settings = Settings(income_cache_ttl=ttl)
                assert settings.income_cache_ttl == ttl

        # 测试无效TTL（负数）
        with patch.dict(os.environ, {"TUSHARE_TOKEN": "dummy"}):
            with pytest.raises(ValidationError):
                Settings(income_cache_ttl=-1)

    def test_settings_log_level_validation(self):
        """测试日志级别验证"""
        # 测试有效日志级别
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        for level in valid_levels:
            with patch.dict(os.environ, {"TUSHARE_TOKEN": "dummy"}):
                settings = Settings(log_level=level)
                assert settings.log_level == level

        # 测试无效日志级别
        with patch.dict(os.environ, {"TUSHARE_TOKEN": "dummy"}):
            with pytest.raises(ValidationError):
                Settings(log_level="INVALID_LEVEL")


class TestGetSettings:
    """测试 get_settings 单例函数"""

    def test_get_settings_singleton(self):
        """测试 get_settings 返回单例"""
        with patch.dict(os.environ, {"TUSHARE_TOKEN": "dummy_token"}):
            settings1 = get_settings()
            settings2 = get_settings()
            assert settings1 is settings2

    def test_get_settings_late_initialization(self):
        """测试延迟初始化"""
        # 先调用 get_settings，再设置环境变量
        with patch.dict(os.environ, {"TUSHARE_TOKEN": "dummy_token"}):
            settings1 = get_settings()

            # 清除全局设置模拟新的初始化
            import tushare_query_mcp.config as config_module

            config_module._settings = None

            with patch.dict(os.environ, {"TUSHARE_TOKEN": "new_token"}):
                settings2 = get_settings()
                # 应该返回同一个实例，不受环境影响
                assert settings1 is not settings2


class TestSettingsEnvironmentPriority:
    """测试配置优先级"""

    def test_env_var_overrides_default(self):
        """测试环境变量覆盖默认值"""
        custom_port = 9999

        with patch.dict(
            os.environ, {"TUSHARE_TOKEN": "dummy_token", "API_PORT": str(custom_port)}
        ):
            settings = Settings()
            assert settings.api_port == custom_port

    def test_constructor_arg_overrides_env(self):
        """测试构造函数参数覆盖环境变量"""
        env_port = 8888
        constructor_port = 7777

        with patch.dict(
            os.environ, {"TUSHARE_TOKEN": "dummy_token", "API_PORT": str(env_port)}
        ):
            settings = Settings(api_port=constructor_port)
            assert settings.api_port == constructor_port


class TestValidateToken:
    """测试 Token 验证函数"""

    def test_valid_token(self):
        """测试有效 token"""
        # 任何非空字符串都是有效的 token
        assert validate_token("any_token") is True
        assert validate_token("123456") is True
        assert validate_token("abc.def-123_xyz") is True
        assert validate_token("a") is True

    def test_invalid_token(self):
        """测试无效 token"""
        # 空字符串
        assert validate_token("") is False
        assert validate_token(None) is False

        # 空白字符串
        assert validate_token("   ") is False
        assert validate_token("\t\n") is False
        assert validate_token(" \r\n  ") is False


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
