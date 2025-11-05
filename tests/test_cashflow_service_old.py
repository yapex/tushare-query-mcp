"""
CashFlowService测试用例
测试现金流量表服务的完整业务逻辑，包括数据获取、缓存、过滤和字段选择
"""

import asyncio
import time
from datetime import datetime
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tushare_query_mcp.schemas.request import CashFlowRequest
from tushare_query_mcp.schemas.response import CashFlowResponse, ResponseStatus
# 导入待测试的模块
from tushare_query_mcp.services.cashflow_service import CashFlowService


class TestCashFlowService:
    """测试CashFlowService类"""

    @pytest.fixture
    def mock_config(self):
        """模拟配置"""
        return {"tushare_token": "test_token_12345"}

    @pytest.fixture
    def mock_tushare_source(self):
        """模拟TushareDataSource"""
        mock_source = AsyncMock()
        # 配置 get_cashflow_data 方法返回数据而不是协程
        mock_source.get_cashflow_data = AsyncMock(return_value=[])
        mock_source.health_check = AsyncMock(return_value={"status": "healthy"})
        return mock_source

    @pytest.fixture
    def mock_cache(self):
        """模拟缓存"""
        mock_cache = MagicMock()  # 使用普通Mock，因为缓存方法是同步的
        # 配置缓存方法返回值
        mock_cache.get.return_value = None
        mock_cache.set.return_value = None
        mock_cache.stats.return_value = {"hits": 0, "misses": 0}
        mock_cache.clear.return_value = 0
        return mock_cache

    @pytest.fixture
    def cashflow_service(self, mock_config, mock_tushare_source, mock_cache):
        """创建CashFlowService实例"""
        with patch(
            "tushare_query_mcp.services.base_service.TushareDataSource"
        ) as mock_datasource_class:
            mock_datasource_class.return_value = mock_tushare_source

            with patch(
                "tushare_query_mcp.services.base_service.cache_manager", mock_cache
            ):
                service = CashFlowService(mock_config["tushare_token"])
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
                "net_cashflows_act": 150000000000.00,
                "net_cashflows_inv_act": -80000000000.00,
                "net_cashflows_fin_act": -30000000000.00,
                "cash_invest_rece": 2000000000.00,
                "fix_asset_invest": -75000000000.00,
                "intang_asset_invest": -5000000000.00,
                "cfa_fr_borr": 100000000000.00,
                "cfa_fr_equiv_invest": -20000000000.00,
                "cfa_fr_oth_fin_act": -10000000000.00,
                "n_cashflow_end": 800000000000.00,
                "n_cashflow_beg": 750000000000.00,
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
                "net_cashflows_act": 120000000000.00,
                "net_cashflows_inv_act": -60000000000.00,
                "net_cashflows_fin_act": -25000000000.00,
                "cash_invest_rece": 1500000000.00,
                "fix_asset_invest": -55000000000.00,
                "intang_asset_invest": -3000000000.00,
                "cfa_fr_borr": 80000000000.00,
                "cfa_fr_equiv_invest": -15000000000.00,
                "cfa_fr_oth_fin_act": -8000000000.00,
                "n_cashflow_end": 750000000000.00,
                "n_cashflow_beg": 700000000000.00,
                "update_flag": "1",
            },
        ]

    @pytest.fixture
    def sample_request(self):
        """示例请求"""
        return CashFlowRequest(
            ts_code="600519.SH",
            fields=[
                "end_date",
                "net_cashflows_act",
                "net_cashflows_inv_act",
                "net_cashflows_fin_act",
            ],
            start_date="20240101",
            end_date="20241231",
        )

    def test_service_initialization(self, mock_config):
        """测试服务初始化"""
        with patch(
            "tushare_query_mcp.services.base_service.TushareDataSource"
        ) as mock_datasource_class:
            service = CashFlowService(mock_config["tushare_token"])

            mock_datasource_class.assert_called_once_with(mock_config["tushare_token"])
            assert service.tushare_source is not None
            assert service.cache is not None

    @pytest.mark.asyncio
    async def test_get_cashflow_data_cache_hit(
        self, cashflow_service, mock_cache, sample_raw_data, sample_request
    ):
        """测试缓存命中场景"""
        # 设置缓存返回数据
        mock_cache.get.return_value = sample_raw_data

        # 调用服务
        start_time = time.time()
        response = await cashflow_service.get_cashflow_data(sample_request)
        end_time = time.time()

        # 验证缓存被调用
        mock_cache.get.assert_called_once()
        cache_key = mock_cache.get.call_args[0][0]
        assert len(cache_key) == 32  # MD5哈希长度
        assert isinstance(cache_key, str)

        # 验证缓存未调用set
        mock_cache.set.assert_not_called()

        # 验证响应
        assert isinstance(response, CashFlowResponse)
        assert response.status == ResponseStatus.SUCCESS
        assert response.from_cache is True
        assert response.data_type == "cashflow"
        assert len(response.data) == 2

        # 验证字段选择
        selected_record = response.data[0]
        assert set(selected_record.keys()) == {
            "end_date",
            "net_cashflows_act",
            "net_cashflows_inv_act",
            "net_cashflows_fin_act",
        }
        assert selected_record["net_cashflows_act"] == 150000000000.00

        # 验证查询时间很短（缓存命中）
        assert response.query_time < 0.01

    @pytest.mark.asyncio
    async def test_get_cashflow_data_cache_miss(
        self,
        cashflow_service,
        mock_cache,
        mock_tushare_source,
        sample_raw_data,
        sample_request,
    ):
        """测试缓存未命中场景"""
        # 设置缓存为空
        mock_cache.get.return_value = None
        mock_tushare_source.get_cashflow_data.return_value = sample_raw_data

        # 调用服务
        response = await cashflow_service.get_cashflow_data(sample_request)

        # 验证缓存查询
        mock_cache.get.assert_called_once()

        # 验证数据源被调用
        mock_tushare_source.get_cashflow_data.assert_called_once()

        # 验证缓存被设置
        mock_cache.set.assert_called_once()
        cache_data = mock_cache.set.call_args[0][1]
        assert cache_data == sample_raw_data

        # 验证响应
        assert response.from_cache is False
        assert response.status == ResponseStatus.SUCCESS
        assert len(response.data) == 2

    @pytest.mark.asyncio
    async def test_get_cashflow_data_with_update_flag_filtering(
        self, cashflow_service, mock_cache, mock_tushare_source
    ):
        """测试update_flag过滤功能"""
        # 设置包含重复记录的原始数据
        raw_data_with_duplicates = [
            {
                "ts_code": "600519.SH",
                "end_date": "20240930",
                "net_cashflows_act": 150000000000.00,
                "update_flag": "1",
            },
            {
                "ts_code": "600519.SH",
                "end_date": "20240930",
                "net_cashflows_act": 150000000000.00,
                "update_flag": "0",  # 重复记录，不同update_flag
            },
        ]

        mock_cache.get.return_value = None
        mock_tushare_source.get_cashflow_data.return_value = raw_data_with_duplicates

        # 创建包含update_flag字段的请求
        request = CashFlowRequest(
            ts_code="600519.SH", fields=["end_date", "net_cashflows_act", "update_flag"]
        )

        # 调用服务
        response = await cashflow_service.get_cashflow_data(request)

        # 验证数据过滤
        assert len(response.data) == 1  # 重复记录被过滤
        assert response.data[0]["update_flag"] == "1"  # 选择了update_flag=1的记录

    @pytest.mark.asyncio
    async def test_get_cashflow_data_field_selection(
        self, cashflow_service, mock_cache, sample_raw_data, sample_request
    ):
        """测试字段选择功能"""
        mock_cache.get.return_value = sample_raw_data

        # 请求特定字段
        response = await cashflow_service.get_cashflow_data(sample_request)

        # 验证只返回请求的字段
        selected_fields = set(response.data[0].keys())
        expected_fields = set(sample_request.fields)
        assert selected_fields == expected_fields

        # 验证字段值正确
        assert response.data[0]["net_cashflows_act"] == 150000000000.00
        assert response.data[0]["net_cashflows_inv_act"] == -80000000000.00

    @pytest.mark.asyncio
    async def test_get_cashflow_data_no_dates(
        self, cashflow_service, mock_cache, sample_raw_data
    ):
        """测试不提供日期范围"""
        mock_cache.get.return_value = sample_raw_data

        request = CashFlowRequest(
            ts_code="600519.SH",
            fields=["end_date", "net_cashflows_act"],
            # 不提供日期范围
        )

        response = await cashflow_service.get_cashflow_data(request)

        # 验证成功响应
        assert response.status == ResponseStatus.SUCCESS
        assert len(response.data) == 2

        # 验证缓存键生成
        mock_cache.get.assert_called_once()
        cache_key = mock_cache.get.call_args[0][0]
        assert len(cache_key) == 32  # MD5哈希长度
        assert isinstance(cache_key, str)

    @pytest.mark.asyncio
    async def test_get_cashflow_data_empty_fields(
        self, cashflow_service, mock_cache, sample_raw_data
    ):
        """测试空字段列表"""
        mock_cache.get.return_value = sample_raw_data

        request = CashFlowRequest(ts_code="600519.SH", fields=[])  # 空字段列表

        response = await cashflow_service.get_cashflow_data(request)

        # 验证返回所有字段
        assert response.status == ResponseStatus.SUCCESS
        assert len(response.data) == 2
        assert len(response.data[0]) > 10  # 应该返回所有字段

    @pytest.mark.asyncio
    async def test_get_cashflow_data_invalid_fields(
        self, cashflow_service, mock_cache, sample_raw_data
    ):
        """测试无效字段"""
        mock_cache.get.return_value = sample_raw_data

        request = CashFlowRequest(
            ts_code="600519.SH",
            fields=[
                "end_date",
                "net_cashflows_act",
                "invalid_field",
                "another_invalid",
            ],
        )

        response = await cashflow_service.get_cashflow_data(request)

        # 验证只返回有效字段
        assert response.status == ResponseStatus.SUCCESS
        selected_fields = set(response.data[0].keys())
        assert selected_fields == {"end_date", "net_cashflows_act"}
        assert "invalid_field" not in selected_fields
        assert "another_invalid" not in selected_fields

    @pytest.mark.asyncio
    async def test_get_cashflow_data_empty_result(
        self, cashflow_service, mock_cache, mock_tushare_source, sample_request
    ):
        """测试空数据结果"""
        mock_cache.get.return_value = None
        mock_tushare_source.get_cashflow_data.return_value = []  # 空结果

        response = await cashflow_service.get_cashflow_data(sample_request)

        # 验证响应
        assert response.status == ResponseStatus.SUCCESS
        assert response.data == []
        assert response.total_records == 0
        assert response.message == "现金流量表查询成功，但无数据"

    @pytest.mark.asyncio
    async def test_get_cashflow_data_tushare_exception(
        self, cashflow_service, mock_cache, mock_tushare_source, sample_request
    ):
        """测试Tushare API异常"""
        mock_cache.get.return_value = None
        mock_tushare_source.get_cashflow_data.side_effect = Exception("API调用失败")

        response = await cashflow_service.get_cashflow_data(sample_request)

        # 验证错误响应
        assert response.status == ResponseStatus.ERROR
        assert response.data == []
        assert "API调用失败" in response.message
        assert response.error is not None

    @pytest.mark.asyncio
    async def test_get_cashflow_data_concurrent_requests(
        self, cashflow_service, mock_cache, mock_tushare_source, sample_raw_data
    ):
        """测试并发请求"""
        mock_cache.get.return_value = None  # 缓存未命中
        mock_tushare_source.get_cashflow_data.return_value = sample_raw_data

        # 创建多个并发请求
        request1 = CashFlowRequest(
            ts_code="600519.SH", fields=["end_date", "net_cashflows_act"]
        )
        request2 = CashFlowRequest(
            ts_code="000001.SZ", fields=["end_date", "net_cashflows_act"]
        )

        # 并发执行
        responses = await asyncio.gather(
            cashflow_service.get_cashflow_data(request1),
            cashflow_service.get_cashflow_data(request2),
        )

        # 验证两个请求都成功
        for response in responses:
            assert response.status == ResponseStatus.SUCCESS
            assert len(response.data) == 2

        # 验证数据源被调用两次
        assert mock_tushare_source.get_cashflow_data.call_count == 2

        # 验证缓存被设置两次
        assert mock_cache.set.call_count == 2

    def test_generate_cache_key(self, cashflow_service, sample_request):
        """测试缓存键生成"""
        cache_key = cashflow_service._generate_cache_key(sample_request)

        # 验证缓存键是有效的MD5哈希
        assert len(cache_key) == 32
        assert isinstance(cache_key, str)
        assert all(c in "0123456789abcdef" for c in cache_key)  # 十六进制字符

    def test_generate_cache_key_different_requests(self, cashflow_service):
        """测试不同请求生成不同的缓存键"""
        request1 = CashFlowRequest(
            ts_code="600519.SH",
            fields=["end_date", "net_cashflows_act"],
            start_date="20240101",
        )
        request2 = CashFlowRequest(
            ts_code="600519.SH",
            fields=["end_date", "net_cashflows_inv_act"],  # 不同字段
            start_date="20240101",
        )

        key1 = cashflow_service._generate_cache_key(request1)
        key2 = cashflow_service._generate_cache_key(request2)

        # 验证不同请求生成不同的缓存键
        assert key1 != key2

    @pytest.mark.asyncio
    async def test_service_health_check(self, cashflow_service, mock_tushare_source):
        """测试服务健康检查"""
        # 设置健康检查返回
        mock_tushare_source.health_check.return_value = {
            "status": "healthy",
            "message": "Tushare API连接正常",
        }

        health_status = await cashflow_service.health_check()

        # 验证健康检查结果
        assert health_status["status"] == "healthy"
        assert health_status["data_source"] == "healthy"
        assert health_status["message"] == "服务运行正常"

    @pytest.mark.asyncio
    async def test_service_health_check_unhealthy(
        self, cashflow_service, mock_tushare_source
    ):
        """测试服务健康检查（不健康状态）"""
        mock_tushare_source.health_check.return_value = {
            "status": "unhealthy",
            "message": "API连接失败",
        }

        health_status = await cashflow_service.health_check()

        # 验证不健康状态
        assert health_status["status"] == "unhealthy"
        assert health_status["data_source"] == "unhealthy"


class TestCashFlowServiceEdgeCases(TestCashFlowService):
    """测试CashFlowService边界情况"""

    @pytest.mark.asyncio
    async def test_get_cashflow_data_malformed_data(
        self, cashflow_service, mock_cache, mock_tushare_source, sample_request
    ):
        """测试处理格式错误的数据"""
        # 设置格式错误的数据
        malformed_data = [
            {"ts_code": "600519.SH", "end_date": "20240930"},  # 缺少关键字段
            {"ts_code": "600519.SH", "end_date": "20240630"},  # 缺少关键字段
        ]

        mock_cache.get.return_value = malformed_data

        response = await cashflow_service.get_cashflow_data(sample_request)

        # 验证服务能处理格式错误的数据
        assert response.status == ResponseStatus.SUCCESS
        # 字段选择器会返回空字典，因为请求的字段都不存在
        assert response.data == [{"end_date": "20240930"}, {"end_date": "20240630"}]

    @pytest.mark.asyncio
    async def test_get_cashflow_data_large_dataset_performance(
        self, cashflow_service, mock_cache, sample_request
    ):
        """测试大数据集性能"""
        # 创建大数据集
        large_data = []
        for i in range(500):
            large_data.append(
                {
                    "ts_code": f"60000{i % 10}.SH",
                    "end_date": "20240930",
                    "net_cashflows_act": 1000000000.0 + i * 1000000,
                    "net_cashflows_inv_act": -500000000.0 + i * 500000,
                    "net_cashflows_fin_act": -200000000.0 + i * 200000,
                    f"extra_field_{i}": f"value_{i}",
                }
            )

        mock_cache.get.return_value = large_data

        # 测试性能
        start_time = time.time()
        response = await cashflow_service.get_cashflow_data(sample_request)
        end_time = time.time()

        processing_time = end_time - start_time

        # 验证性能要求
        assert processing_time < 0.5, f"处理时间过长: {processing_time:.3f}秒"
        assert response.status == ResponseStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_get_cashflow_data_cache_key_collision(
        self,
        cashflow_service,
        mock_cache,
        mock_tushare_source,
        sample_raw_data,
        sample_request,
    ):
        """测试缓存键冲突处理"""
        # 模拟缓存键冲突的情况
        mock_cache.get.return_value = None  # 缓存未命中
        mock_tushare_source.get_cashflow_data.return_value = sample_raw_data

        response = await cashflow_service.get_cashflow_data(sample_request)

        # 验证缓存被正确设置
        mock_cache.set.assert_called_once()
        assert response.from_cache is False


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
