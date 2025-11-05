"""
TushareDataSource测试用例
测试数据源的初始化、API调用封装和异步查询功能
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tushare_query_mcp.schemas.request import (BalanceDataSourceRequest,
                                               CashFlowDataSourceRequest,
                                               IncomeDataSourceRequest,
                                               StockDataSourceRequest)
# 导入待测试的模块
from tushare_query_mcp.services.tushare_datasource import TushareDataSource


class TestTushareDataSource:
    """测试TushareDataSource类"""

    @pytest.fixture
    def mock_config(self):
        """模拟配置"""
        return {"tushare_token": "test_token_12345"}

    @pytest.fixture
    def mock_tushare_pro(self):
        """模拟tushare pro对象"""
        mock_pro = MagicMock()
        return mock_pro

    @pytest.fixture
    def tushare_source(self, mock_config, mock_tushare_pro):
        """创建TushareDataSource实例"""
        with patch(
            "tushare_query_mcp.services.tushare_datasource.ts.set_token"
        ) as mock_set_token:
            with patch(
                "tushare_query_mcp.services.tushare_datasource.ts.pro_api",
                return_value=mock_tushare_pro,
            ):
                source = TushareDataSource(mock_config["tushare_token"])
                return source

    def test_initialization_success(self, mock_config):
        """测试成功初始化"""
        with patch(
            "tushare_query_mcp.services.tushare_datasource.ts.set_token"
        ) as mock_set_token:
            with patch(
                "tushare_query_mcp.services.tushare_datasource.ts.pro_api"
            ) as mock_pro_api:
                source = TushareDataSource(mock_config["tushare_token"])

                mock_set_token.assert_called_once_with(mock_config["tushare_token"])
                mock_pro_api.assert_called_once()
                assert source.token == mock_config["tushare_token"]
                assert source.pro is not None

    def test_initialization_empty_token(self):
        """测试空token初始化"""
        with pytest.raises(ValueError, match="Tushare token不能为空"):
            TushareDataSource("")

    def test_initialization_none_token(self):
        """测试None token初始化"""
        with pytest.raises(ValueError, match="Tushare token不能为空"):
            TushareDataSource(None)

    @pytest.mark.asyncio
    async def test_get_income_data_success(self, tushare_source, mock_tushare_pro):
        """测试成功获取利润表数据"""
        # 模拟API返回数据
        mock_data = [
            {
                "ts_code": "600519.SH",
                "ann_date": "20241030",
                "end_date": "20240930",
                "report_type": "1",
                "comp_type": "1",
                "basic_eps": 15.33,
                "n_income_attr_p": 19223784414.08,
            },
            {
                "ts_code": "600519.SH",
                "ann_date": "20240718",
                "end_date": "20240630",
                "report_type": "1",
                "comp_type": "1",
                "basic_eps": 14.78,
                "n_income_attr_p": 18555488059.34,
            },
        ]

        # 设置mock返回值
        mock_tushare_pro.income = MagicMock(return_value=mock_data)

        # 创建请求
        request = IncomeDataSourceRequest(
            ts_code="600519.SH", start_date="20240101", end_date="20241231"
        )

        # 调用方法
        result = await tushare_source.get_income_data(request)

        # 验证调用
        mock_tushare_pro.income.assert_called_once_with(
            ts_code="600519.SH", start_date="20240101", end_date="20241231"
        )

        # 验证结果
        assert result == mock_data
        assert len(result) == 2
        assert result[0]["ts_code"] == "600519.SH"
        assert result[0]["end_date"] == "20240930"

    @pytest.mark.asyncio
    async def test_get_income_data_no_dates(self, tushare_source, mock_tushare_pro):
        """测试不提供日期范围获取利润表数据"""
        mock_data = [
            {
                "ts_code": "600519.SH",
                "end_date": "20240930",
                "n_income_attr_p": 19223784414.08,
            }
        ]

        mock_tushare_pro.income = MagicMock(return_value=mock_data)

        request = IncomeDataSourceRequest(ts_code="600519.SH")
        result = await tushare_source.get_income_data(request)

        # 验证调用时只传递ts_code参数
        mock_tushare_pro.income.assert_called_once_with(ts_code="600519.SH")
        assert result == mock_data

    @pytest.mark.asyncio
    async def test_get_balance_data_success(self, tushare_source, mock_tushare_pro):
        """测试成功获取资产负债表数据"""
        mock_data = [
            {
                "ts_code": "600519.SH",
                "end_date": "20240930",
                "total_assets": 2000000000000.00,
                "total_liab": 500000000000.00,
            }
        ]

        mock_tushare_pro.balancesheet = MagicMock(return_value=mock_data)

        request = BalanceDataSourceRequest(ts_code="600519.SH")
        result = await tushare_source.get_balance_data(request)

        mock_tushare_pro.balancesheet.assert_called_once_with(ts_code="600519.SH")
        assert result == mock_data

    @pytest.mark.asyncio
    async def test_get_cashflow_data_success(self, tushare_source, mock_tushare_pro):
        """测试成功获取现金流量表数据"""
        mock_data = [
            {
                "ts_code": "600519.SH",
                "end_date": "20240930",
                "n_cashflow_act": 50000000000.00,
            }
        ]

        mock_tushare_pro.cashflow = MagicMock(return_value=mock_data)

        request = CashFlowDataSourceRequest(ts_code="600519.SH")
        result = await tushare_source.get_cashflow_data(request)

        mock_tushare_pro.cashflow.assert_called_once_with(ts_code="600519.SH")
        assert result == mock_data

    @pytest.mark.asyncio
    async def test_get_stock_data_success(self, tushare_source, mock_tushare_pro):
        """测试成功获取股票基本信息数据"""
        mock_data = [
            {
                "ts_code": "600519.SH",
                "symbol": "600519",
                "name": "贵州茅台",
                "area": "贵州",
                "industry": "白酒",
                "market": "主板",
            }
        ]

        mock_tushare_pro.stock_basic = MagicMock(return_value=mock_data)

        request = StockDataSourceRequest(ts_code="600519.SH")
        result = await tushare_source.get_stock_data(request)

        mock_tushare_pro.stock_basic.assert_called_once_with(ts_code="600519.SH")
        assert result == mock_data

    @pytest.mark.asyncio
    async def test_api_call_exception(self, tushare_source, mock_tushare_pro):
        """测试API调用异常处理"""
        # 模拟API异常
        mock_tushare_pro.income.side_effect = Exception("API调用失败")

        request = IncomeDataSourceRequest(ts_code="600519.SH")

        with pytest.raises(Exception, match="API调用失败"):
            await tushare_source.get_income_data(request)

    @pytest.mark.asyncio
    async def test_api_call_empty_result(self, tushare_source, mock_tushare_pro):
        """测试API返回空结果"""
        mock_tushare_pro.income = MagicMock(return_value=[])

        request = IncomeDataSourceRequest(ts_code="600519.SH")
        result = await tushare_source.get_income_data(request)

        assert result == []
        mock_tushare_pro.income.assert_called_once_with(ts_code="600519.SH")

    @pytest.mark.asyncio
    async def test_multiple_concurrent_requests(self, tushare_source, mock_tushare_pro):
        """测试并发请求处理"""
        # 设置不同的返回数据
        mock_tushare_pro.income = MagicMock(
            side_effect=[
                [{"ts_code": "600519.SH", "end_date": "20240930"}],
                [{"ts_code": "000001.SZ", "end_date": "20240930"}],
            ]
        )

        # 创建多个并发请求
        request1 = IncomeDataSourceRequest(ts_code="600519.SH")
        request2 = IncomeDataSourceRequest(ts_code="000001.SZ")

        # 并发执行
        results = await asyncio.gather(
            tushare_source.get_income_data(request1),
            tushare_source.get_income_data(request2),
        )

        # 验证结果
        assert len(results) == 2
        assert results[0][0]["ts_code"] == "600519.SH"
        assert results[1][0]["ts_code"] == "000001.SZ"

        # 验证API被调用两次
        assert mock_tushare_pro.income.call_count == 2

    def test_build_api_parameters_with_dates(self):
        """测试构建API参数（包含日期）"""
        with patch("tushare_query_mcp.services.tushare_datasource.ts.set_token"):
            with patch("tushare_query_mcp.services.tushare_datasource.ts.pro_api"):
                source = TushareDataSource("test_token")

                request = IncomeDataSourceRequest(
                    ts_code="600519.SH", start_date="20240101", end_date="20241231"
                )

                params = source._build_api_parameters(request)
                expected = {
                    "ts_code": "600519.SH",
                    "start_date": "20240101",
                    "end_date": "20241231",
                }
                assert params == expected

    def test_build_api_parameters_without_dates(self):
        """测试构建API参数（不包含日期）"""
        with patch("tushare_query_mcp.services.tushare_datasource.ts.set_token"):
            with patch("tushare_query_mcp.services.tushare_datasource.ts.pro_api"):
                source = TushareDataSource("test_token")

                request = IncomeDataSourceRequest(ts_code="600519.SH")

                params = source._build_api_parameters(request)
                expected = {"ts_code": "600519.SH"}
                assert params == expected

    @pytest.mark.asyncio
    async def test_get_all_financial_data(self, tushare_source, mock_tushare_pro):
        """测试获取所有财务数据（利润表、资产负债表、现金流量表）"""
        # 设置mock返回数据
        mock_tushare_pro.income = MagicMock(
            return_value=[{"ts_code": "600519.SH", "end_date": "20240930"}]
        )
        mock_tushare_pro.balancesheet = MagicMock(
            return_value=[{"ts_code": "600519.SH", "end_date": "20240930"}]
        )
        mock_tushare_pro.cashflow = MagicMock(
            return_value=[{"ts_code": "600519.SH", "end_date": "20240930"}]
        )

        request = IncomeDataSourceRequest(ts_code="600519.SH")

        # 并发获取所有财务数据
        income_task = tushare_source.get_income_data(request)
        balance_task = tushare_source.get_balance_data(
            BalanceDataSourceRequest(ts_code="600519.SH")
        )
        cashflow_task = tushare_source.get_cashflow_data(
            CashFlowDataSourceRequest(ts_code="600519.SH")
        )

        income_data, balance_data, cashflow_data = await asyncio.gather(
            income_task, balance_task, cashflow_task
        )

        # 验证所有API都被调用
        mock_tushare_pro.income.assert_called_once()
        mock_tushare_pro.balancesheet.assert_called_once()
        mock_tushare_pro.cashflow.assert_called_once()

        # 验证返回数据
        assert len(income_data) == 1
        assert len(balance_data) == 1
        assert len(cashflow_data) == 1


class TestTushareDataSourceIntegration:
    """集成测试类"""

    @pytest.mark.asyncio
    async def test_real_api_connection(self):
        """测试真实API连接（仅在有真实token时运行）"""
        # 这个测试需要真实的tushare token，在CI环境中跳过
        pytest.skip("需要真实tushare token，在CI环境中跳过")

    @pytest.mark.asyncio
    async def test_error_recovery(self):
        """测试错误恢复机制"""
        # 这个测试验证网络错误后的重试逻辑
        pytest.skip("需要实现重试机制后添加")


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
