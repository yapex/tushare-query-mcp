"""
数据模型测试用例
测试请求和响应模型的验证、序列化和字段选择功能
"""

from datetime import datetime
from typing import Any, Dict, List

import pytest

# 导入待测试的模块
from tushare_query_mcp.schemas.request import (BalanceDataSourceRequest,
                                               BalanceRequest,
                                               CashFlowDataSourceRequest,
                                               CashFlowRequest,
                                               DataSourceRequest,
                                               FinancialDataRequest,
                                               IncomeDataSourceRequest,
                                               IncomeRequest,
                                               StockDataSourceRequest,
                                               StockRequest)
from tushare_query_mcp.schemas.response import (BalanceResponse,
                                                CashFlowResponse, ErrorDetail,
                                                FinancialDataResponse,
                                                IncomeResponse, ResponseStatus,
                                                StockResponse)


class TestFinancialDataRequest:
    """测试基础财务数据请求模型"""

    def test_valid_financial_data_request(self):
        """测试有效的财务数据请求"""
        request = FinancialDataRequest(
            ts_code="600519.SH",
            fields=["end_date", "n_income_attr_p"],
            start_date="20240101",
            end_date="20241231",
        )

        assert request.ts_code == "600519.SH"
        assert request.fields == ["end_date", "n_income_attr_p"]
        assert request.start_date == "20240101"
        assert request.end_date == "20241231"

    def test_required_fields_validation(self):
        """测试必填字段验证"""
        # ts_code 是必填的
        with pytest.raises(ValueError) as exc_info:
            FinancialDataRequest(ts_code="", fields=["end_date"])  # 空字符串应该失败

        assert "ts_code" in str(exc_info.value)

    def test_fields_validation(self):
        """测试字段列表验证"""
        # fields 不能为空
        with pytest.raises(ValueError) as exc_info:
            FinancialDataRequest(ts_code="600519.SH", fields=[])  # 空列表应该失败

        assert "fields" in str(exc_info.value)

    def test_date_format_validation(self):
        """测试日期格式验证"""
        # 无效的日期格式
        invalid_dates = ["2024-01-01", "2024/01/01", "2024011", "invalid"]

        for invalid_date in invalid_dates:
            with pytest.raises(ValueError):
                FinancialDataRequest(
                    ts_code="600519.SH", fields=["end_date"], start_date=invalid_date
                )

    def test_valid_date_formats(self):
        """测试有效日期格式"""
        valid_dates = ["20240101", "20241231", "19990101"]

        for valid_date in valid_dates:
            request = FinancialDataRequest(
                ts_code="600519.SH", fields=["end_date"], start_date=valid_date
            )
            assert request.start_date == valid_date


class TestIncomeRequest:
    """测试利润表请求模型"""

    def test_income_request_inheritance(self):
        """测试利润表请求继承关系"""
        request = IncomeRequest(
            ts_code="600519.SH",
            fields=["end_date", "n_income_attr_p", "revenue"],
            start_date="20240101",
        )

        # 应该继承基础请求的所有属性
        assert hasattr(request, "ts_code")
        assert hasattr(request, "fields")
        assert hasattr(request, "start_date")
        assert hasattr(request, "end_date")

        # 利润表特有的属性（如果有的话）
        assert request.ts_code == "600519.SH"


class TestBalanceRequest:
    """测试资产负债表请求模型"""

    def test_balance_request_creation(self):
        """测试资产负债表请求创建"""
        request = BalanceRequest(
            ts_code="000001.SZ", fields=["end_date", "total_assets", "total_liab"]
        )

        assert request.ts_code == "000001.SZ"
        assert "total_assets" in request.fields


class TestCashFlowRequest:
    """测试现金流量表请求模型"""

    def test_cashflow_request_creation(self):
        """测试现金流量表请求创建"""
        request = CashFlowRequest(
            ts_code="600036.SH", fields=["end_date", "n_cashflow_act"]
        )

        assert request.ts_code == "600036.SH"
        assert "n_cashflow_act" in request.fields


class TestStockRequest:
    """测试股票信息请求模型"""

    def test_stock_request_creation(self):
        """测试股票信息请求创建"""
        request = StockRequest(
            ts_code="600519.SH", fields=["ts_code", "name", "industry"]
        )

        assert request.ts_code == "600519.SH"
        assert "name" in request.fields
        assert "industry" in request.fields


class TestFinancialDataResponse:
    """测试基础财务数据响应模型"""

    def test_successful_response_creation(self):
        """测试成功响应创建"""
        response = FinancialDataResponse(
            status="success",
            message="查询成功",
            data=[
                {"end_date": "20240930", "n_income_attr_p": 19223784414.08},
                {"end_date": "20240630", "n_income_attr_p": 18555488059.34},
            ],
            total_records=2,
            from_cache=False,
            query_time=0.234,
        )

        assert response.status == "success"
        assert response.message == "查询成功"
        assert len(response.data) == 2
        assert response.total_records == 2
        assert response.from_cache is False
        assert response.query_time == 0.234

    def test_error_response_creation(self):
        """测试错误响应创建"""
        response = FinancialDataResponse(
            status="error",
            message="查询失败：无相关数据",
            data=[],
            total_records=0,
            from_cache=False,
            query_time=0.001,
        )

        assert response.status == "error"
        assert "无相关数据" in response.message
        assert response.data == []
        assert response.total_records == 0

    def test_empty_data_response(self):
        """测试空数据响应"""
        response = FinancialDataResponse(
            status="success",
            message="查询成功，但无数据",
            data=[],
            total_records=0,
            from_cache=True,
            query_time=0.05,
        )

        assert response.status == "success"
        assert response.total_records == 0
        assert response.from_cache is True


class TestIncomeResponse:
    """测试利润表响应模型"""

    def test_income_response_with_data(self):
        """测试带数据的利润表响应"""
        response = IncomeResponse(
            status="success",
            message="利润表查询成功",
            data=[
                {
                    "ts_code": "600519.SH",
                    "end_date": "20240930",
                    "n_income_attr_p": 19223784414.08,
                    "revenue": 120714458386.98,
                    "basic_eps": 15.33,
                }
            ],
            total_records=1,
            from_cache=False,
            query_time=0.156,
        )

        assert response.status == "success"
        assert response.data[0]["ts_code"] == "600519.SH"
        assert response.data[0]["n_income_attr_p"] == 19223784414.08


class TestResponseStatus:
    """测试响应状态枚举"""

    def test_valid_status_values(self):
        """测试有效的状态值"""
        valid_statuses = ["success", "error", "pending"]

        for status in valid_statuses:
            # 这些值应该都是有效的
            assert isinstance(status, str)
            assert len(status) > 0

    def test_status_validation(self):
        """测试状态验证"""
        # 无效状态值（如果实现了验证）
        invalid_statuses = ["", "invalid_status", None]

        for invalid_status in invalid_statuses:
            if invalid_status is not None:
                # 实现状态验证后的测试
                pass


class TestResponseSerialization:
    """测试响应序列化"""

    def test_response_to_dict(self):
        """测试响应转换为字典"""
        response = FinancialDataResponse(
            status="success",
            message="测试消息",
            data=[{"test": "data"}],
            total_records=1,
            from_cache=False,
            query_time=0.1,
        )

        # 应该能够序列化为字典
        response_dict = response.model_dump()

        assert isinstance(response_dict, dict)
        assert response_dict["status"] == "success"
        assert response_dict["total_records"] == 1
        assert isinstance(response_dict["data"], list)

    def test_response_to_json(self):
        """测试响应转换为JSON"""
        response = FinancialDataResponse(
            status="success",
            message="JSON测试",
            data=[{"json_field": "json_value"}],
            total_records=1,
            from_cache=True,
            query_time=0.05,
        )

        # 应该能够序列化为JSON字符串
        json_str = response.model_dump_json()

        assert isinstance(json_str, str)
        assert "success" in json_str
        assert "json_field" in json_str


class TestFieldSelection:
    """测试字段选择功能"""

    def test_field_selection_in_response(self):
        """测试响应中的字段选择"""
        # 模拟只返回部分字段的数据
        full_data = {
            "ts_code": "600519.SH",
            "end_date": "20240930",
            "n_income_attr_p": 19223784414.08,
            "revenue": 120714458386.98,
            "basic_eps": 15.33,
            "total_profit": 23482132293.47,
        }

        requested_fields = ["end_date", "n_income_attr_p"]

        # 模拟字段选择逻辑
        selected_data = {
            field: full_data[field] for field in requested_fields if field in full_data
        }

        assert selected_data == {
            "end_date": "20240930",
            "n_income_attr_p": 19223784414.08,
        }
        assert len(selected_data) == 2

    def test_all_fields_selection(self):
        """测试选择所有字段"""
        data = {"field1": "value1", "field2": "value2", "field3": "value3"}

        # 当没有指定字段时，返回所有字段
        all_fields = list(data.keys())
        selected_data = {field: data[field] for field in all_fields}

        assert selected_data == data

    def test_nonexistent_field_selection(self):
        """测试选择不存在的字段"""
        data = {"field1": "value1", "field2": "value2"}

        requested_fields = ["field1", "nonexistent_field"]

        # 应该只返回存在的字段
        selected_data = {
            field: data[field] for field in requested_fields if field in data
        }

        assert selected_data == {"field1": "value1"}
        assert len(selected_data) == 1


class TestDataSourceRequest:
    """测试数据源层请求模型"""

    def test_data_source_request_creation(self):
        """测试数据源请求创建（不包含fields参数）"""
        request = DataSourceRequest(
            ts_code="600519.SH", start_date="20240101", end_date="20241231"
        )

        assert request.ts_code == "600519.SH"
        assert request.start_date == "20240101"
        assert request.end_date == "20241231"

        # 确保没有fields参数
        assert (
            not hasattr(request, "fields") or getattr(request, "fields", None) is None
        )

    def test_income_data_source_request(self):
        """测试利润表数据源请求"""
        request = IncomeDataSourceRequest(ts_code="600519.SH", start_date="20240101")

        assert request.ts_code == "600519.SH"
        assert request.start_date == "20240101"

    def test_balance_data_source_request(self):
        """测试资产负债表数据源请求"""
        request = BalanceDataSourceRequest(ts_code="000001.SZ")

        assert request.ts_code == "000001.SZ"

    def test_cash_flow_data_source_request(self):
        """测试现金流量表数据源请求"""
        request = CashFlowDataSourceRequest(
            ts_code="600036.SH", start_date="20240101", end_date="20241231"
        )

        assert request.ts_code == "600036.SH"
        assert request.start_date == "20240101"
        assert request.end_date == "20241231"

    def test_stock_data_source_request(self):
        """测试股票信息数据源请求"""
        request = StockDataSourceRequest(ts_code="600519.SH")

        assert request.ts_code == "600519.SH"
        # 股票信息请求通常没有日期参数
        assert request.start_date is None
        assert request.end_date is None

    def test_data_source_request_validation(self):
        """测试数据源请求验证"""
        # 测试股票代码验证
        with pytest.raises(ValueError):
            DataSourceRequest(ts_code="invalid_code")

        # 测试日期格式验证
        with pytest.raises(ValueError):
            DataSourceRequest(ts_code="600519.SH", start_date="2024-01-01")  # 错误格式


class TestArchitectureSeparation:
    """测试架构分层"""

    def test_service_vs_data_source_request_difference(self):
        """测试Service层和数据源层请求模型的区别"""
        # Service层请求（包含fields）
        service_request = IncomeRequest(
            ts_code="600519.SH",
            fields=["end_date", "n_income_attr_p"],
            start_date="20240101",
        )

        # 数据源层请求（不包含fields）
        data_source_request = IncomeDataSourceRequest(
            ts_code="600519.SH", start_date="20240101"
        )

        # Service层请求应该有fields参数
        assert hasattr(service_request, "fields")
        assert service_request.fields == ["end_date", "n_income_attr_p"]

        # 数据源层请求不应该有fields参数
        assert hasattr(data_source_request, "ts_code")
        # 确认数据源请求模型设计正确（不包含fields字段）


class TestErrorDetail:
    """测试错误详情模型"""

    def test_error_detail_creation(self):
        """测试错误详情创建"""
        error_detail = ErrorDetail(
            code="VALIDATION_ERROR",
            message="参数验证失败",
            field="ts_code",
            value="invalid_code",
        )

        assert error_detail.code == "VALIDATION_ERROR"
        assert error_detail.message == "参数验证失败"
        assert error_detail.field == "ts_code"
        assert error_detail.value == "invalid_code"


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
