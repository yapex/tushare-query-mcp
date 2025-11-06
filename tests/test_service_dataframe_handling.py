"""
服务层DataFrame处理测试
测试服务层正确处理来自DataSource的数据，避免布尔值模糊性错误
"""

from unittest.mock import AsyncMock, Mock, patch

import pandas as pd
import pytest

from tushare_query_mcp.schemas.request import (BalanceRequest, CashFlowRequest,
                                               IncomeRequest)
from tushare_query_mcp.services.balance_service import BalanceService
from tushare_query_mcp.services.cashflow_service import CashFlowService
from tushare_query_mcp.services.income_service import IncomeService


class TestServiceDataFrameHandling:
    """测试服务层DataFrame处理"""

    @pytest.fixture
    def mock_tushare_source(self):
        """模拟TushareDataSource"""
        mock_source = AsyncMock()
        return mock_source

    @pytest.fixture
    def income_service(self, mock_tushare_source):
        """创建IncomeService实例 - 使用依赖注入"""
        return IncomeService(mock_tushare_source)

    @pytest.fixture
    def balance_service(self, mock_tushare_source):
        """创建BalanceService实例 - 使用依赖注入"""
        return BalanceService(mock_tushare_source)

    @pytest.fixture
    def cashflow_service(self, mock_tushare_source):
        """创建CashFlowService实例 - 使用依赖注入"""
        return CashFlowService(mock_tushare_source)

    @pytest.mark.asyncio
    async def test_income_service_handles_empty_dataframe(
        self, income_service, mock_tushare_source
    ):
        """测试IncomeService处理空DataFrame"""
        # 模拟空DataFrame
        empty_df = pd.DataFrame()
        mock_tushare_source.get_income_data.return_value = empty_df

        request = IncomeRequest(
            ts_code="600519.SH", fields=["end_date", "total_revenue"]
        )

        result = await income_service.get_income_data(request)

        # 验证结果
        assert result.data == []
        assert result.total_records == 0
        assert "无数据" in result.message

    @pytest.mark.asyncio
    async def test_income_service_handles_dataframe_data(
        self, income_service, mock_tushare_source
    ):
        """测试IncomeService处理DataFrame数据"""
        # 模拟DataFrame数据
        test_data = pd.DataFrame(
            {
                "ts_code": ["600519.SH", "600519.SH"],
                "end_date": ["20240331", "20231231"],
                "total_revenue": [1000000000.0, 900000000.0],
                "n_income_attr_p": [500000000.0, 450000000.0],
            }
        )
        mock_tushare_source.get_income_data.return_value = test_data

        request = IncomeRequest(
            ts_code="600519.SH", fields=["end_date", "total_revenue", "n_income_attr_p"]
        )

        result = await income_service.get_income_data(request)

        # 验证结果
        assert len(result.data) == 2
        assert result.total_records == 2
        assert all(isinstance(record, dict) for record in result.data)
        assert result.data[0]["total_revenue"] == 1000000000.0
        assert result.data[1]["total_revenue"] == 900000000.0

    @pytest.mark.asyncio
    async def test_balance_service_handles_empty_data(
        self, balance_service, mock_tushare_source
    ):
        """测试BalanceService处理空数据"""
        # 模拟空列表
        mock_tushare_source.get_balance_data.return_value = []

        request = BalanceRequest(
            ts_code="600519.SH", fields=["end_date", "total_assets"]
        )

        result = await balance_service.get_balance_data(request)

        assert result.data == []
        assert result.total_records == 0

    @pytest.mark.asyncio
    async def test_cashflow_service_handles_list_data(
        self, cashflow_service, mock_tushare_source
    ):
        """测试CashFlowService处理列表数据"""
        # 模拟字典列表数据
        test_data = [
            {
                "ts_code": "600519.SH",
                "end_date": "20240331",
                "net_cashflows_act": 600000000.0,
                "net_cashflows_inv_act": -200000000.0,
            }
        ]
        mock_tushare_source.get_cashflow_data.return_value = test_data

        request = CashFlowRequest(
            ts_code="600519.SH",
            fields=["end_date", "net_cashflows_act", "net_cashflows_inv_act"],
        )

        result = await cashflow_service.get_cashflow_data(request)

        assert len(result.data) == 1
        assert result.data[0]["net_cashflows_act"] == 600000000.0

    @pytest.mark.asyncio
    async def test_service_error_handling(self, income_service, mock_tushare_source):
        """测试服务层错误处理"""
        # 模拟DataSource异常
        mock_tushare_source.get_income_data.side_effect = Exception("数据库连接失败")

        request = IncomeRequest(
            ts_code="600519.SH", fields=["end_date", "total_revenue"]
        )

        result = await income_service.get_income_data(request)

        assert result.status == "error"
        assert "数据库连接失败" in result.error.message

    @pytest.mark.asyncio
    async def test_field_selection_with_dataframe(
        self, income_service, mock_tushare_source
    ):
        """测试DataFrame的字段选择"""
        # 模拟包含多个字段的DataFrame
        test_data = pd.DataFrame(
            {
                "ts_code": ["600519.SH", "600519.SH"],
                "ann_date": ["20240430", "20230430"],
                "end_date": ["20240331", "20231231"],
                "total_revenue": [1000000000.0, 900000000.0],
                "n_income_attr_p": [500000000.0, 450000000.0],
                "basic_eps": [10.5, 9.8],
                "extra_field": ["extra1", "extra2"],  # 不在请求字段中的额外字段
            }
        )
        mock_tushare_source.get_income_data.return_value = test_data

        # 只请求部分字段
        request = IncomeRequest(
            ts_code="600519.SH", fields=["end_date", "total_revenue", "basic_eps"]
        )

        result = await income_service.get_income_data(request)

        # 验证只包含请求的字段
        assert len(result.data) == 2
        for record in result.data:
            assert set(record.keys()) == {"end_date", "total_revenue", "basic_eps"}
            assert "extra_field" not in record
            assert "ann_date" not in record

    def test_data_empty_check_logic(self):
        """测试数据空值检查逻辑"""
        # 测试DataFrame的空值检查
        empty_df = pd.DataFrame()
        non_empty_df = pd.DataFrame({"a": [1, 2, 3]})

        # 模拟服务层的空值检查逻辑
        def check_data_empty(data):
            if hasattr(data, "empty") and data.empty:
                return True
            elif hasattr(data, "__len__") and len(data) == 0:
                return True
            else:
                return False

        assert check_data_empty(empty_df) == True
        assert check_data_empty(non_empty_df) == False
        assert check_data_empty([]) == True
        assert check_data_empty([1, 2, 3]) == False

    @pytest.mark.asyncio
    async def test_available_fields_with_empty_data(
        self, income_service, mock_tushare_source
    ):
        """测试在无数据时获取可用字段"""
        # 模拟空数据
        mock_tushare_source.get_income_data.return_value = pd.DataFrame()

        result = await income_service.get_available_fields("600519.SH")

        # 应该返回空列表
        assert result == []

    @pytest.mark.asyncio
    async def test_available_fields_with_dataframe_data(
        self, income_service, mock_tushare_source
    ):
        """测试从DataFrame获取可用字段"""
        # 模拟包含多个字段的DataFrame
        test_data = pd.DataFrame(
            {
                "ts_code": ["600519.SH"],
                "end_date": ["20240331"],
                "total_revenue": [1000000000.0],
                "n_income_attr_p": [500000000.0],
                "basic_eps": [10.5],
            }
        )
        mock_tushare_source.get_income_data.return_value = test_data

        result = await income_service.get_available_fields("600519.SH")

        # 应该返回所有字段
        expected_fields = [
            "ts_code",
            "end_date",
            "total_revenue",
            "n_income_attr_p",
            "basic_eps",
        ]
        assert set(result) == set(expected_fields)
