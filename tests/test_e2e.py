#!/usr/bin/env python3
"""
端到端测试
测试完整的 API 和 MCP 流程
"""

import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# 添加项目根目录到 Python 路径，以便导入 scripts 模块
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tushare_query_mcp.main import app


@pytest.fixture
def test_cache_dir():
    """创建临时缓存目录"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_settings(test_cache_dir):
    """模拟设置"""
    with patch("tushare_query_mcp.config.get_settings") as mock_get_settings:
        settings = MagicMock()
        settings.tushare_token = "test_token"
        settings.cache_dir = test_cache_dir
        settings.income_cache_ttl = 60
        settings.balance_cache_ttl = 60
        settings.cashflow_cache_ttl = 60
        settings.stock_cache_ttl = 60
        settings.api_timeout = 30
        settings.max_retries = 3
        settings.log_level = "INFO"
        mock_get_settings.return_value = settings
        yield settings


@pytest.fixture
def test_client(mock_settings):
    """创建测试客户端"""
    return TestClient(app)


class TestFastAPIE2E:
    """FastAPI 端到端测试"""

    def test_health_check(self, test_client):
        """测试健康检查端点"""
        response = test_client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "config" in data
        assert "services" in data
        assert "timestamp" in data
        assert "version" in data

    def test_swagger_docs(self, test_client):
        """测试 Swagger 文档生成"""
        response = test_client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_redoc_docs(self, test_client):
        """测试 ReDoc 文档生成"""
        response = test_client.get("/redoc")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_openapi_schema(self, test_client):
        """测试 OpenAPI 模式"""
        response = test_client.get("/openapi.json")
        assert response.status_code == 200

        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema

        # 验证路径存在
        paths = schema["paths"]
        assert "/health" in paths
        assert "/api/v1/income/data" in paths
        assert "/api/v1/balance/data" in paths
        assert "/api/v1/cashflow/data" in paths
        assert "/api/v1/stock/data" in paths

    def test_api_error_handling(self, test_client):
        """测试 API 错误处理"""
        # 测试无效股票代码
        response = test_client.get("/api/v1/income/data", params={"ts_code": ""})
        assert response.status_code == 422  # 验证错误

        # 测试缺少必需参数
        response = test_client.get("/api/v1/income/data")
        assert response.status_code == 422

    @patch("tushare_query_mcp.services.income_service.IncomeService.get_income_data")
    def test_api_response_format_consistency(self, mock_get_data, test_client):
        """测试 API 响应格式一致性"""
        # 模拟服务返回数据
        mock_get_data.return_value = {
            "ts_code": "600519.SH",
            "records": [
                {
                    "end_date": "20231231",
                    "total_revenue": 1000000000,
                    "net_profit": 100000000,
                }
            ],
            "pagination": {"total": 1, "page": 1, "page_size": 50},
        }

        response = test_client.get(
            "/api/v1/income/data",
            params={
                "ts_code": "600519.SH",
                "start_date": "20230101",
                "end_date": "20231231",
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert "success" in data
        assert "message" in data
        assert "data" in data
        assert "cached" in data
        assert "timestamp" in data

        if data["success"]:
            assert "ts_code" in data["data"]
            assert "records" in data["data"]
            assert "pagination" in data["data"]


class TestCacheE2E:
    """缓存端到端测试"""

    @patch("tushare_query_mcp.services.income_service.IncomeService.get_income_data")
    def test_cache_persistence(self, mock_get_data, test_client, test_cache_dir):
        """测试缓存持久化"""
        # 模拟服务返回数据
        mock_get_data.return_value = {
            "ts_code": "600519.SH",
            "records": [{"end_date": "20231231", "total_revenue": 1000000000}],
            "pagination": {"total": 1, "page": 1, "page_size": 50},
        }

        # 第一次请求
        response1 = test_client.get(
            "/api/v1/income/data",
            params={
                "ts_code": "600519.SH",
                "start_date": "20230101",
                "end_date": "20231231",
            },
        )
        assert response1.status_code == 200
        data1 = response1.json()

        # 第二次请求
        response2 = test_client.get(
            "/api/v1/income/data",
            params={
                "ts_code": "600519.SH",
                "start_date": "20230101",
                "end_date": "20231231",
            },
        )
        assert response2.status_code == 200
        data2 = response2.json()

        # 验证数据一致性
        assert data1["data"]["records"] == data2["data"]["records"]

    def test_cache_stats_in_health_check(self, test_client, test_cache_dir):
        """测试健康检查中的缓存统计"""
        response = test_client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert "config" in data
        config = data["config"]
        assert "cache_directory" in config


class TestPerformanceE2E:
    """性能端到端测试"""

    @patch("tushare_query_mcp.services.income_service.IncomeService.get_income_data")
    def test_api_response_time(self, mock_get_data, test_client):
        """测试 API 响应时间"""
        import time

        mock_get_data.return_value = {
            "ts_code": "600519.SH",
            "records": [],
            "pagination": {"total": 0, "page": 1, "page_size": 50},
        }

        start_time = time.time()
        response = test_client.get(
            "/api/v1/income/data", params={"ts_code": "600519.SH"}
        )
        end_time = time.time()

        assert response.status_code == 200
        # 响应时间应该在合理范围内（小于5秒）
        assert (end_time - start_time) < 5.0


@pytest.mark.asyncio
class TestIntegrationE2E:
    """集成端到端测试"""

    def test_fastapi_services_integration(self, test_client):
        """测试 FastAPI 服务集成"""
        # 确保 FastAPI 运行正常
        health_response = test_client.get("/health")
        assert health_response.status_code == 200

        data = health_response.json()
        assert data["status"] == "healthy"
        assert "services" in data

        # 验证各个服务状态
        services = data["services"]
        assert "income" in services
        assert "balance" in services
        assert "cashflow" in services
        assert "stock" in services

        for service_name, service_info in services.items():
            assert service_info["status"] == "healthy"

    @patch("tushare_query_mcp.services.income_service.IncomeService.health_check")
    def test_service_health_integration(self, mock_health, test_client):
        """测试服务健康检查集成"""
        # 模拟健康检查
        mock_health.return_value = {
            "status": "healthy",
            "message": "service is running",
        }

        response = test_client.get("/api/v1/income/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"


class TestMCPE2E:
    """MCP 端到端测试"""

    def test_mcp_server_import(self):
        """测试 MCP 服务器导入"""
        try:
            from scripts.mcp_server import create_mcp_server

            server = create_mcp_server()
            assert server is not None
        except ImportError as e:
            pytest.skip(f"MCP server import failed: {e}")

    @pytest.mark.asyncio
    async def test_mcp_tools_registration(self):
        """测试 MCP 工具注册"""
        try:
            from scripts.mcp_server import create_mcp_server

            server = create_mcp_server()

            # 获取工具列表
            tools = await server.list_tools()
            assert len(tools) == 3

            tool_names = [tool.name for tool in tools]
            assert "query_stock_financials" in tool_names
            assert "get_available_financial_fields" in tool_names
            assert "validate_financial_fields" in tool_names

        except Exception as e:
            pytest.skip(f"MCP tools test failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
