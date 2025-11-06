"""
IncomeService测试用例
测试利润表服务的完整业务逻辑，包括数据获取、过滤和字段选择
DataSource层已处理缓存，Service层专注于业务逻辑处理。
"""

import asyncio
import time
from datetime import datetime
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tushare_query_mcp.schemas.request import IncomeRequest
from tushare_query_mcp.schemas.response import IncomeResponse, ResponseStatus
# 导入待测试的模块
from tushare_query_mcp.services.income_service import IncomeService


class TestIncomeService:
    """测试IncomeService类"""

    @pytest.fixture
    def mock_config(self):
        """模拟配置"""
        return {"tushare_token": "test_token_12345"}

    @pytest.fixture
    def mock_tushare_source(self):
        """模拟TushareDataSource"""
        mock_source = AsyncMock()
        # 配置 get_income_data 方法返回数据而不是协程
        mock_source.get_income_data = AsyncMock(return_value=[])
        mock_source.health_check = AsyncMock(return_value={"status": "healthy"})
        return mock_source

    @pytest.fixture
    def income_service(self, mock_tushare_source):
        """创建IncomeService实例 - 使用依赖注入"""
        # 直接注入mock数据源，避免使用patch
        service = IncomeService(mock_tushare_source)
        return service

    @pytest.fixture
    def sample_raw_data(self):
        """示例原始数据（从TushareDataSource获取）"""
        return [
            {
                "ts_code": "600519.SH",
                "ann_date": "20241030",
                "f_ann_date": "20241030",
                "end_date": "20240930",
                "report_type": "1",
                "comp_type": "1",
                "end_type": "4",
                "basic_eps": 15.33,
                "diluted_eps": 15.33,
                "total_revenue": 120714458386.98,
                "revenue": 120714458386.98,
                "n_income_attr_p": 19223784414.08,
                "total_profit": 23482132293.47,
                "income_tax": 4258347879.39,
                "n_income": 19223784414.08,
                "ebit": 23482132293.47,
                "ebitda": 23482132293.47,
                "update_flag": "1",
            },
            {
                "ts_code": "600519.SH",
                "ann_date": "20240718",
                "f_ann_date": "20240718",
                "end_date": "20240630",
                "report_type": "1",
                "comp_type": "1",
                "end_type": "4",
                "basic_eps": 12.85,
                "diluted_eps": 12.85,
                "total_revenue": 81931724607.68,
                "revenue": 81931724607.68,
                "n_income_attr_p": 15746684414.08,
                "total_profit": 19842132293.47,
                "income_tax": 4095447879.39,
                "n_income": 15746684414.08,
                "ebit": 19842132293.47,
                "ebitda": 19842132293.47,
                "update_flag": "1",
            },
        ]

    @pytest.fixture
    def sample_request(self):
        """示例请求"""
        return IncomeRequest(
            ts_code="600519.SH",
            fields=["end_date", "total_revenue", "n_income_attr_p"],
            start_date="20240101",
            end_date="20241231",
        )

    def test_service_initialization(self, mock_config):
        """测试服务初始化"""
        with patch(
            "tushare_query_mcp.services.income_service.TushareDataSource"
        ) as mock_datasource_class:
            service = IncomeService(mock_config["tushare_token"])

            mock_datasource_class.assert_called_once_with(mock_config["tushare_token"])
            assert service.data_source is not None
            assert service.service_name == "利润表"

    @pytest.mark.asyncio
    async def test_get_income_data_with_update_flag_filtering(
        self, income_service, mock_tushare_source
    ):
        """测试update_flag过滤功能"""
        # 设置包含重复记录的原始数据
        raw_data_with_duplicates = [
            {
                "ts_code": "600519.SH",
                "end_date": "20240930",
                "total_revenue": 120714458386.98,
                "update_flag": "1",
            },
            {
                "ts_code": "600519.SH",
                "end_date": "20240930",
                "total_revenue": 120714458386.98,
                "update_flag": "0",  # 重复记录，不同update_flag
            },
        ]

        mock_tushare_source.get_income_data.return_value = raw_data_with_duplicates

        # 创建包含update_flag字段的请求
        request = IncomeRequest(
            ts_code="600519.SH", fields=["end_date", "total_revenue", "update_flag"]
        )

        # 调用服务
        response = await income_service.get_income_data(request)

        # 验证数据过滤
        assert len(response.data) == 1  # 重复记录被过滤
        assert response.data[0]["update_flag"] == "1"  # 选择了update_flag=1的记录

    @pytest.mark.asyncio
    async def test_get_income_data_field_selection(
        self, income_service, mock_tushare_source, sample_raw_data, sample_request
    ):
        """测试字段选择功能"""
        mock_tushare_source.get_income_data.return_value = sample_raw_data

        # 请求特定字段
        response = await income_service.get_income_data(sample_request)

        # 验证只返回请求的字段
        selected_fields = set(response.data[0].keys())
        expected_fields = set(sample_request.fields)
        assert selected_fields == expected_fields

        # 验证字段值正确
        assert response.data[0]["total_revenue"] == 120714458386.98
        assert response.data[0]["n_income_attr_p"] == 19223784414.08

    @pytest.mark.asyncio
    async def test_get_income_data_no_dates(
        self, income_service, mock_tushare_source, sample_raw_data
    ):
        """测试不提供日期范围"""
        mock_tushare_source.get_income_data.return_value = sample_raw_data

        request = IncomeRequest(
            ts_code="600519.SH",
            fields=["end_date", "total_revenue"],
            # 不提供日期范围
        )

        response = await income_service.get_income_data(request)

        # 验证成功响应
        assert response.status == ResponseStatus.SUCCESS
        assert len(response.data) == 2

    @pytest.mark.asyncio
    async def test_get_income_data_empty_fields(
        self, income_service, mock_tushare_source, sample_raw_data
    ):
        """测试空字段列表"""
        mock_tushare_source.get_income_data.return_value = sample_raw_data

        request = IncomeRequest(ts_code="600519.SH", fields=[])  # 空字段列表

        response = await income_service.get_income_data(request)

        # 验证返回所有字段
        assert response.status == ResponseStatus.SUCCESS
        assert len(response.data) == 2
        assert len(response.data[0]) > 10  # 应该返回所有字段

    @pytest.mark.asyncio
    async def test_get_income_data_invalid_fields(
        self, income_service, mock_tushare_source, sample_raw_data
    ):
        """测试无效字段"""
        mock_tushare_source.get_income_data.return_value = sample_raw_data

        request = IncomeRequest(
            ts_code="600519.SH",
            fields=["end_date", "total_revenue", "invalid_field", "another_invalid"],
        )

        response = await income_service.get_income_data(request)

        # 验证只返回有效字段
        assert response.status == ResponseStatus.SUCCESS
        selected_fields = set(response.data[0].keys())
        assert selected_fields == {"end_date", "total_revenue"}
        assert "invalid_field" not in selected_fields
        assert "another_invalid" not in selected_fields

    @pytest.mark.asyncio
    async def test_get_income_data_empty_result(
        self, income_service, mock_tushare_source, sample_request
    ):
        """测试空数据结果"""
        mock_tushare_source.get_income_data.return_value = []  # 空结果

        response = await income_service.get_income_data(sample_request)

        # 验证响应
        assert response.status == ResponseStatus.SUCCESS
        assert response.data == []
        assert response.total_records == 0
        assert response.message == "利润表查询成功，但无数据"

    @pytest.mark.asyncio
    async def test_get_income_data_tushare_exception(
        self, income_service, mock_tushare_source, sample_request
    ):
        """测试Tushare API异常"""
        mock_tushare_source.get_income_data.side_effect = Exception("API调用失败")

        response = await income_service.get_income_data(sample_request)

        # 验证错误响应
        assert response.status == ResponseStatus.ERROR
        assert response.data == []
        assert "API调用失败" in response.message
        assert response.error is not None

    @pytest.mark.asyncio
    async def test_get_income_data_concurrent_requests(
        self, income_service, mock_tushare_source, sample_raw_data
    ):
        """测试并发请求"""
        mock_tushare_source.get_income_data.return_value = sample_raw_data

        # 创建多个并发请求
        request1 = IncomeRequest(
            ts_code="600519.SH", fields=["end_date", "total_revenue"]
        )
        request2 = IncomeRequest(
            ts_code="000001.SZ", fields=["end_date", "total_revenue"]
        )

        # 并发执行
        responses = await asyncio.gather(
            income_service.get_income_data(request1),
            income_service.get_income_data(request2),
        )

        # 验证两个请求都成功
        for response in responses:
            assert response.status == ResponseStatus.SUCCESS
            assert len(response.data) == 2

        # 验证数据源被调用两次
        assert mock_tushare_source.get_income_data.call_count == 2

    @pytest.mark.asyncio
    async def test_get_income_data_with_report_type(
        self, income_service, mock_tushare_source, sample_raw_data
    ):
        """测试报告类型过滤"""
        mock_tushare_source.get_income_data.return_value = sample_raw_data

        # 创建包含报告类型的请求
        request = IncomeRequest(
            ts_code="600519.SH",
            fields=["end_date", "total_revenue", "report_type"],
            report_type="1",
        )

        response = await income_service.get_income_data(request)

        # 验证请求成功
        assert response.status == ResponseStatus.SUCCESS
        assert len(response.data) == 2

    @pytest.mark.asyncio
    async def test_service_health_check(self, income_service, mock_tushare_source):
        """测试服务健康检查"""
        # 设置健康检查返回
        mock_tushare_source.health_check.return_value = {
            "status": "healthy",
            "message": "Tushare API连接正常",
        }

        health_status = await income_service.health_check()

        # 验证健康检查结果
        assert health_status["status"] == "healthy"
        assert health_status["data_source"] == "healthy"
        assert health_status["message"] == "服务运行正常"

    @pytest.mark.asyncio
    async def test_service_health_check_unhealthy(
        self, income_service, mock_tushare_source
    ):
        """测试服务健康检查（不健康状态）"""
        mock_tushare_source.health_check.return_value = {
            "status": "unhealthy",
            "message": "API连接失败",
        }

        health_status = await income_service.health_check()

        # 验证不健康状态
        assert health_status["status"] == "unhealthy"
        assert health_status["data_source"] == "unhealthy"


class TestIncomeServiceEdgeCases(TestIncomeService):
    """测试IncomeService边界情况"""

    @pytest.mark.asyncio
    async def test_get_income_data_malformed_data(
        self, income_service, mock_tushare_source, sample_request
    ):
        """测试处理格式错误的数据"""
        # 设置格式错误的数据
        malformed_data = [
            {"ts_code": "600519.SH", "end_date": "20240930"},  # 缺少关键字段
            {"ts_code": "600519.SH", "end_date": "20240630"},  # 缺少关键字段
        ]

        mock_tushare_source.get_income_data.return_value = malformed_data

        response = await income_service.get_income_data(sample_request)

        # 验证服务能处理格式错误的数据
        assert response.status == ResponseStatus.SUCCESS
        # 字段选择器会返回空字典，因为请求的字段都不存在
        assert response.data == [{"end_date": "20240930"}, {"end_date": "20240630"}]

    @pytest.mark.asyncio
    async def test_get_income_data_large_dataset_performance(
        self, income_service, mock_tushare_source, sample_request
    ):
        """测试大数据集性能"""
        # 创建大数据集
        large_data = []
        for i in range(500):
            large_data.append(
                {
                    "ts_code": f"60000{i % 10}.SH",
                    "end_date": "20240930",
                    "total_revenue": 1000000000.0 + i * 1000000,
                    "n_income_attr_p": 100000000.0 + i * 100000,
                    f"extra_field_{i}": f"value_{i}",
                }
            )

        mock_tushare_source.get_income_data.return_value = large_data

        # 测试性能
        start_time = time.time()
        response = await income_service.get_income_data(sample_request)
        end_time = time.time()

        processing_time = end_time - start_time

        # 验证性能要求
        assert processing_time < 0.5, f"处理时间过长: {processing_time:.3f}秒"
        assert response.status == ResponseStatus.SUCCESS


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
