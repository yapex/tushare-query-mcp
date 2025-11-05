"""
TushareDataSource DataFrame处理测试
测试DataFrame转换为字典列表的逻辑，确保不会出现布尔值模糊性错误
"""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pandas as pd
import pytest

from tushare_query_mcp.schemas.request import (BalanceDataSourceRequest,
                                               CashFlowDataSourceRequest,
                                               IncomeDataSourceRequest)
from tushare_query_mcp.services.tushare_datasource import TushareDataSource


class TestDataFrameHandling:
    """测试DataFrame处理逻辑"""

    @pytest.fixture
    def mock_pro_api(self):
        """模拟Tushare Pro API"""
        mock_pro = Mock()
        return mock_pro

    @pytest.fixture
    def data_source(self, mock_pro_api):
        """创建TushareDataSource实例"""
        with patch("tushare_query_mcp.services.tushare_datasource.ts") as mock_ts:
            mock_ts.set_token = Mock()
            data_source = TushareDataSource("test_token")
            data_source.pro = mock_pro_api
            return data_source

    @pytest.mark.asyncio
    async def test_income_dataframe_conversion(self, data_source, mock_pro_api):
        """测试利润表DataFrame转换为字典列表"""
        # 创建模拟的DataFrame数据
        test_data = pd.DataFrame(
            {
                "ts_code": ["600519.SH", "600519.SH"],
                "ann_date": ["20240430", "20230430"],
                "end_date": ["20240331", "20230331"],
                "total_revenue": [1000000000.0, 900000000.0],
                "n_income_attr_p": [500000000.0, 450000000.0],
            }
        )

        # 模拟API调用返回DataFrame
        mock_pro_api.income.return_value = test_data

        # 创建请求
        request = IncomeDataSourceRequest(
            ts_code="600519.SH", start_date="20230101", end_date="20241231"
        )

        # 调用方法
        result = await data_source.get_income_data(request)

        # 验证结果
        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(record, dict) for record in result)
        assert result[0]["ts_code"] == "600519.SH"
        assert result[0]["total_revenue"] == 1000000000.0

    @pytest.mark.asyncio
    async def test_balance_dataframe_conversion(self, data_source, mock_pro_api):
        """测试资产负债表DataFrame转换为字典列表"""
        test_data = pd.DataFrame(
            {
                "ts_code": ["600519.SH"],
                "ann_date": ["20240430"],
                "end_date": ["20240331"],
                "total_assets": [2000000000.0],
                "total_liab": [800000000.0],
                "total_equity": [1200000000.0],
            }
        )

        mock_pro_api.balancesheet.return_value = test_data

        request = BalanceDataSourceRequest(
            ts_code="600519.SH", start_date="20230101", end_date="20241231"
        )

        result = await data_source.get_balance_data(request)

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], dict)
        assert result[0]["total_assets"] == 2000000000.0

    @pytest.mark.asyncio
    async def test_cashflow_dataframe_conversion(self, data_source, mock_pro_api):
        """测试现金流量表DataFrame转换为字典列表"""
        test_data = pd.DataFrame(
            {
                "ts_code": ["600519.SH"],
                "ann_date": ["20240430"],
                "end_date": ["20240331"],
                "net_cashflows_act": [600000000.0],
                "net_cashflows_inv_act": [-200000000.0],
                "net_cashflows_fin_act": [100000000.0],
            }
        )

        mock_pro_api.cashflow.return_value = test_data

        request = CashFlowDataSourceRequest(
            ts_code="600519.SH", start_date="20230101", end_date="20241231"
        )

        result = await data_source.get_cashflow_data(request)

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], dict)
        assert result[0]["net_cashflows_act"] == 600000000.0

    @pytest.mark.asyncio
    async def test_empty_dataframe_handling(self, data_source, mock_pro_api):
        """测试空DataFrame的处理"""
        # 创建空DataFrame
        empty_data = pd.DataFrame()

        mock_pro_api.income.return_value = empty_data

        request = IncomeDataSourceRequest(
            ts_code="000001.SZ", start_date="20230101", end_date="20231231"
        )

        result = await data_source.get_income_data(request)

        # 空DataFrame应该被转换为空列表
        assert isinstance(result, list)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_api_returns_list_already(self, data_source, mock_pro_api):
        """测试API已经返回列表的情况"""
        # API已经返回字典列表
        list_data = [
            {
                "ts_code": "600519.SH",
                "end_date": "20240331",
                "total_revenue": 1000000000.0,
            }
        ]

        mock_pro_api.income.return_value = list_data

        request = IncomeDataSourceRequest(
            ts_code="600519.SH", start_date="20240101", end_date="20241231"
        )

        result = await data_source.get_income_data(request)

        # 应该原样返回
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["ts_code"] == "600519.SH"

    @pytest.mark.asyncio
    async def test_data_frame_with_null_values(self, data_source, mock_pro_api):
        """测试包含空值的DataFrame"""
        test_data = pd.DataFrame(
            {
                "ts_code": ["600519.SH", "600519.SH"],
                "ann_date": ["20240430", None],
                "end_date": ["20240331", "20231231"],
                "total_revenue": [1000000000.0, None],
                "n_income_attr_p": [500000000.0, 450000000.0],
            }
        )

        mock_pro_api.income.return_value = test_data

        request = IncomeDataSourceRequest(
            ts_code="600519.SH", start_date="20230101", end_date="20241231"
        )

        result = await data_source.get_income_data(request)

        assert isinstance(result, list)
        assert len(result) == 2
        # NaN在DataFrame转换为字典时会被转换为float('nan')
        import math

        assert result[1]["ann_date"] is None
        assert isinstance(result[1]["total_revenue"], float) and math.isnan(
            result[1]["total_revenue"]
        )

    @pytest.mark.asyncio
    async def test_api_exception_handling(self, data_source, mock_pro_api):
        """测试API异常情况下的处理"""
        # 模拟API调用异常
        mock_pro_api.income.side_effect = Exception("API调用失败")

        request = IncomeDataSourceRequest(
            ts_code="600519.SH", start_date="20240101", end_date="20241231"
        )

        # 应该抛出异常
        with pytest.raises(Exception, match="API调用失败"):
            await data_source.get_income_data(request)

    def test_dataframe_to_dict_conversion_method(self):
        """测试DataFrame转换为字典列表的独立方法"""
        # 测试普通DataFrame
        test_data = pd.DataFrame(
            {
                "ts_code": ["600519.SH", "600519.SH"],
                "total_revenue": [1000000000.0, 900000000.0],
            }
        )

        # 模拟转换逻辑
        if hasattr(test_data, "to_dict"):
            result = test_data.to_dict("records")
        else:
            result = test_data

        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(record, dict) for record in result)
        assert result[0]["ts_code"] == "600519.SH"
        assert result[1]["total_revenue"] == 900000000.0

    def test_empty_dataframe_check_methods(self):
        """测试各种数据类型的空值检查方法"""
        # 测试空DataFrame
        empty_df = pd.DataFrame()
        assert hasattr(empty_df, "empty")
        assert empty_df.empty == True

        # 测试非空DataFrame
        non_empty_df = pd.DataFrame({"a": [1, 2, 3]})
        assert hasattr(non_empty_df, "empty")
        assert non_empty_df.empty == False

        # 测试空列表
        empty_list = []
        assert hasattr(empty_list, "__len__")
        assert len(empty_list) == 0

        # 测试非空列表
        non_empty_list = [{"a": 1}]
        assert hasattr(non_empty_list, "__len__")
        assert len(non_empty_list) > 0
