"""
数据过滤器测试用例
测试update_flag过滤功能
"""

from typing import Any, Dict, List

import pytest

# 导入待测试的模块
from tushare_query_mcp.utils.data_filter import filter_by_update_flag


class TestUpdateFlagFilter:
    """测试update_flag过滤器"""

    @pytest.fixture
    def sample_data(self):
        """示例数据，包含重复记录"""
        return [
            {
                "ts_code": "600519.SH",
                "end_date": "20241231",
                "update_flag": "1",
                "n_income_attr_p": 19223784414.08,
                "revenue": 120714458386.98,
            },
            {
                "ts_code": "600519.SH",
                "end_date": "20241231",
                "update_flag": "0",
                "n_income_attr_p": 19223784414.08,
                "revenue": 120714458386.98,
            },
            {
                "ts_code": "600519.SH",
                "end_date": "20240930",
                "update_flag": "1",
                "n_income_attr_p": 18555488059.34,
                "revenue": 100000000000.00,
            },
            {
                "ts_code": "000001.SZ",
                "end_date": "20241231",
                "update_flag": "1",
                "n_income_attr_p": 1000000000.00,
                "revenue": 5000000000.00,
            },
        ]

    def test_filter_by_update_flag_with_duplicates(self, sample_data):
        """测试有重复记录时的update_flag过滤"""
        result = filter_by_update_flag(sample_data)

        # 应该有3条记录：600519.SH的20241231(取update_flag=1)、20240930，以及000001.SZ的20241231
        assert len(result) == 3

        # 检查600519.SH的20241231记录选择了update_flag=1的
        maotai_2024 = next(
            (
                r
                for r in result
                if r["ts_code"] == "600519.SH" and r["end_date"] == "20241231"
            ),
            None,
        )
        assert maotai_2024 is not None
        assert maotai_2024["update_flag"] == "1"

        # 检查600519.SH的20240930记录保留
        maotai_2023 = next(
            (
                r
                for r in result
                if r["ts_code"] == "600519.SH" and r["end_date"] == "20240930"
            ),
            None,
        )
        assert maotai_2023 is not None

        # 检查000001.SZ的记录保留
        ping_an = next((r for r in result if r["ts_code"] == "000001.SZ"), None)
        assert ping_an is not None

    def test_filter_by_update_flag_no_duplicates(self):
        """测试没有重复记录时的处理"""
        data = [
            {
                "ts_code": "600519.SH",
                "end_date": "20241231",
                "update_flag": "1",
                "n_income_attr_p": 19223784414.08,
            },
            {
                "ts_code": "000001.SZ",
                "end_date": "20241231",
                "update_flag": "0",
                "n_income_attr_p": 1000000000.00,
            },
        ]

        result = filter_by_update_flag(data)
        assert len(result) == 2
        assert result[0]["ts_code"] == "600519.SH"
        assert result[1]["ts_code"] == "000001.SZ"

    def test_filter_by_update_flag_no_update_flag_1(self):
        """测试没有update_flag=1记录时的处理"""
        data = [
            {
                "ts_code": "600519.SH",
                "end_date": "20241231",
                "update_flag": "0",
                "n_income_attr_p": 19223784414.08,
            },
            {
                "ts_code": "600519.SH",
                "end_date": "20241231",
                "update_flag": "0",
                "n_income_attr_p": 19223784414.08,
            },
        ]

        result = filter_by_update_flag(data)
        assert len(result) == 1
        assert result[0]["ts_code"] == "600519.SH"
        assert result[0]["update_flag"] == "0"

    def test_filter_by_update_flag_empty_data(self):
        """测试空数据处理"""
        result = filter_by_update_flag([])
        assert result == []

    def test_missing_key_fields(self):
        """测试缺少关键字段的情况"""
        data = [
            {
                "ts_code": "600519.SH",
                # 缺少end_date
                "update_flag": "1",
                "n_income_attr_p": 19223784414.08,
            },
            {
                # 缺少ts_code
                "end_date": "20241231",
                "update_flag": "1",
                "n_income_attr_p": 1000000000.00,
            },
        ]

        result = filter_by_update_flag(data)
        # 都应该被过滤掉
        assert len(result) == 0


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
