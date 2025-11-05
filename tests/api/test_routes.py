"""
FastAPI路由测试
测试所有财务数据API端点的功能、参数验证、错误处理等
"""

import json
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from tushare_query_mcp.api.v1.balance import router as balance_router
from tushare_query_mcp.api.v1.cashflow import router as cashflow_router
# 导入测试相关的模块
from tushare_query_mcp.api.v1.income import router as income_router


class TestIncomeRoutes:
    """测试利润表API路由"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(income_router, prefix="/api/v1/income", tags=["income"])
        return TestClient(app)

    @pytest.fixture
    def mock_income_service(self):
        """模拟IncomeService"""
        mock_service = AsyncMock()
        mock_service.get_income_data.return_value = {
            "status": "success",
            "data": [
                {
                    "end_date": "20240930",
                    "total_revenue": 120714458386.98,
                    "n_income_attr_p": 19223784414.08,
                }
            ],
            "total_records": 1,
            "message": "利润表查询成功",
            "from_cache": False,
            "query_time": 0.123,
            "error": None,
        }
        return mock_service

    def test_get_income_data_success(self, client, mock_income_service):
        """测试成功获取利润表数据"""
        with patch(
            "tushare_query_mcp.api.v1.income.IncomeService",
            return_value=mock_income_service,
        ):
            response = client.get(
                "/api/v1/income/data?ts_code=600519.SH&fields=end_date,total_revenue,n_income_attr_p"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert len(data["data"]) == 1
            assert data["data"][0]["total_revenue"] == 120714458386.98

    def test_get_income_data_missing_ts_code(self, client):
        """测试缺少股票代码参数"""
        response = client.get("/api/v1/income/data?fields=end_date,total_revenue")

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert "ts_code" in str(data["detail"])

    def test_get_income_data_invalid_ts_code(self, client):
        """测试无效的股票代码格式"""
        response = client.get(
            "/api/v1/income/data?ts_code=invalid&fields=end_date,total_revenue"
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_get_income_data_invalid_date_format(self, client):
        """测试无效的日期格式"""
        response = client.get(
            "/api/v1/income/data?ts_code=600519.SH&fields=end_date,total_revenue&start_date=2024-13-01"
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_get_income_data_date_range_validation(self, client):
        """测试日期范围验证（结束日期不能早于开始日期）"""
        response = client.get(
            "/api/v1/income/data?ts_code=600519.SH&fields=end_date,total_revenue&start_date=20241231&end_date=20240101"
        )

        assert response.status_code == 400
        data = response.json()
        assert "结束日期不能早于开始日期" in data["detail"]

    def test_get_income_data_too_many_fields(self, client):
        """测试字段数量限制"""
        fields = ["field" + str(i) for i in range(51)]  # 51个字段，超过限制
        fields_str = ",".join(fields)
        response = client.get(
            f"/api/v1/income/data?ts_code=600519.SH&fields={fields_str}"
        )

        assert response.status_code == 400
        data = response.json()
        assert "字段数量不能超过50个" in data["detail"]

    def test_get_income_data_service_error(self, client, mock_income_service):
        """测试服务层错误"""
        mock_income_service.get_income_data.side_effect = Exception("服务内部错误")

        with patch(
            "tushare_query_mcp.api.v1.income.IncomeService",
            return_value=mock_income_service,
        ):
            response = client.get(
                "/api/v1/income/data?ts_code=600519.SH&fields=end_date,total_revenue"
            )

            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "服务内部错误" in data["detail"]

    def test_get_income_data_empty_result(self, client, mock_income_service):
        """测试空数据结果"""
        mock_income_service.get_income_data.return_value = {
            "status": "success",
            "data": [],
            "total_records": 0,
            "message": "利润表查询成功，但无数据",
            "from_cache": False,
            "query_time": 0.123,
            "error": None,
        }

        with patch(
            "tushare_query_mcp.api.v1.income.IncomeService",
            return_value=mock_income_service,
        ):
            response = client.get(
                "/api/v1/income/data?ts_code=600519.SH&fields=end_date,total_revenue"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["data"] == []
            assert data["total_records"] == 0

    def test_get_income_data_with_all_params(self, client, mock_income_service):
        """测试包含所有参数的请求"""
        with patch(
            "tushare_query_mcp.api.v1.income.IncomeService",
            return_value=mock_income_service,
        ):
            response = client.get(
                "/api/v1/income/data?ts_code=600519.SH&fields=end_date,total_revenue&start_date=20240101&end_date=20241231&report_type=1"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"

    def test_get_income_health_check(self, client, mock_income_service):
        """测试健康检查端点"""
        mock_income_service.health_check.return_value = {
            "status": "healthy",
            "message": "服务运行正常",
            "data_source": "healthy",
            "timestamp": 1234567890.123,
        }

        with patch(
            "tushare_query_mcp.api.v1.income.IncomeService",
            return_value=mock_income_service,
        ):
            response = client.get("/api/v1/income/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["data_source"] == "healthy"


class TestBalanceRoutes:
    """测试资产负债表API路由"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(balance_router, prefix="/api/v1/balance", tags=["balance"])
        return TestClient(app)

    @pytest.fixture
    def mock_balance_service(self):
        """模拟BalanceService"""
        mock_service = AsyncMock()
        mock_service.get_balance_data.return_value = {
            "status": "success",
            "data": [
                {
                    "end_date": "20240930",
                    "total_assets": 2000000000000.00,
                    "total_equity": 1500000000000.00,
                }
            ],
            "total_records": 1,
            "message": "资产负债表查询成功",
            "from_cache": False,
            "query_time": 0.156,
            "error": None,
        }
        return mock_service

    def test_get_balance_data_success(self, client, mock_balance_service):
        """测试成功获取资产负债表数据"""
        with patch(
            "tushare_query_mcp.api.v1.balance.BalanceService",
            return_value=mock_balance_service,
        ):
            response = client.get(
                "/api/v1/balance/data?ts_code=600519.SH&fields=end_date,total_assets,total_equity"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert len(data["data"]) == 1
            assert data["data"][0]["total_assets"] == 2000000000000.00

    def test_get_balance_data_missing_ts_code(self, client):
        """测试缺少股票代码参数"""
        response = client.get("/api/v1/balance/data?fields=end_date,total_assets")

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_get_balance_health_check(self, client, mock_balance_service):
        """测试健康检查端点"""
        mock_balance_service.health_check.return_value = {
            "status": "healthy",
            "message": "服务运行正常",
            "data_source": "healthy",
            "timestamp": 1234567890.123,
        }

        with patch(
            "tushare_query_mcp.api.v1.balance.BalanceService",
            return_value=mock_balance_service,
        ):
            response = client.get("/api/v1/balance/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"


class TestCashFlowRoutes:
    """测试现金流量表API路由"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(
            cashflow_router, prefix="/api/v1/cashflow", tags=["cashflow"]
        )
        return TestClient(app)

    @pytest.fixture
    def mock_cashflow_service(self):
        """模拟CashFlowService"""
        mock_service = AsyncMock()
        mock_service.get_cashflow_data.return_value = {
            "status": "success",
            "data": [
                {
                    "end_date": "20240930",
                    "net_cashflows_act": 150000000000.00,
                    "net_cashflows_inv_act": -80000000000.00,
                }
            ],
            "total_records": 1,
            "message": "现金流量表查询成功",
            "from_cache": False,
            "query_time": 0.145,
            "error": None,
        }
        return mock_service

    def test_get_cashflow_data_success(self, client, mock_cashflow_service):
        """测试成功获取现金流量表数据"""
        with patch(
            "tushare_query_mcp.api.v1.cashflow.CashFlowService",
            return_value=mock_cashflow_service,
        ):
            response = client.get(
                "/api/v1/cashflow/data?ts_code=600519.SH&fields=end_date,net_cashflows_act,net_cashflows_inv_act"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert len(data["data"]) == 1
            assert data["data"][0]["net_cashflows_act"] == 150000000000.00

    def test_get_cashflow_data_missing_ts_code(self, client):
        """测试缺少股票代码参数"""
        response = client.get("/api/v1/cashflow/data?fields=end_date,net_cashflows_act")

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_get_cashflow_health_check(self, client, mock_cashflow_service):
        """测试健康检查端点"""
        mock_cashflow_service.health_check.return_value = {
            "status": "healthy",
            "message": "服务运行正常",
            "data_source": "healthy",
            "timestamp": 1234567890.123,
        }

        with patch(
            "tushare_query_mcp.api.v1.cashflow.CashFlowService",
            return_value=mock_cashflow_service,
        ):
            response = client.get("/api/v1/cashflow/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"


class TestRoutesIntegration:
    """测试路由集成"""

    def test_all_routes_accessible(self):
        """测试所有路由都可以访问"""
        from fastapi import FastAPI

        app = FastAPI()

        # 注册所有路由
        app.include_router(income_router, prefix="/api/v1/income", tags=["income"])
        app.include_router(balance_router, prefix="/api/v1/balance", tags=["balance"])
        app.include_router(
            cashflow_router, prefix="/api/v1/cashflow", tags=["cashflow"]
        )

        client = TestClient(app)

        # 测试所有健康检查端点
        health_endpoints = [
            "/api/v1/income/health",
            "/api/v1/balance/health",
            "/api/v1/cashflow/health",
        ]

        for endpoint in health_endpoints:
            # 这些端点会因为Service未实例化而失败，但应该返回500而不是404
            response = client.get(endpoint)
            assert response.status_code in [
                500,
                200,
            ]  # 500表示路由存在但服务未配置，200表示正常

    def test_api_response_format_consistency(self):
        """测试API响应格式一致性"""
        # 这个测试将在API实现后添加，确保所有API返回相同的响应格式
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
