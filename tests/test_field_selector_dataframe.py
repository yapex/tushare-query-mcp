"""
FieldSelector DataFrame处理测试
测试FieldSelector正确处理DataFrame数据，避免布尔值模糊性错误
"""

import pandas as pd
import pytest

from tushare_query_mcp.utils.field_selector import FieldSelector


class TestFieldSelectorDataFrameHandling:
    """测试FieldSelector的DataFrame处理"""

    def test_select_fields_from_dataframe(self):
        """测试从DataFrame选择字段"""
        # 创建测试DataFrame
        test_data = pd.DataFrame(
            {
                "ts_code": ["600519.SH", "600519.SH"],
                "end_date": ["20240331", "20231231"],
                "total_revenue": [1000000000.0, 900000000.0],
                "n_income_attr_p": [500000000.0, 450000000.0],
                "basic_eps": [10.5, 9.8],
                "extra_field": ["extra1", "extra2"],
            }
        )

        # 选择部分字段
        selected_fields = ["end_date", "total_revenue", "basic_eps"]
        result = FieldSelector.select_fields(test_data, selected_fields)

        # 验证结果
        assert isinstance(result, list)
        assert len(result) == 2

        # 验证每条记录只包含选择的字段
        for record in result:
            assert set(record.keys()) == {"end_date", "total_revenue", "basic_eps"}
            assert "extra_field" not in record
            assert "ts_code" not in record

    def test_select_fields_from_empty_dataframe(self):
        """测试从空DataFrame选择字段"""
        empty_df = pd.DataFrame()

        result = FieldSelector.select_fields(empty_df, ["end_date", "total_revenue"])

        # 应该返回空列表
        assert result == []

    def test_select_fields_from_empty_list(self):
        """测试从空列表选择字段"""
        empty_list = []

        result = FieldSelector.select_fields(empty_list, ["end_date", "total_revenue"])

        # 应该返回空列表
        assert result == []

    def test_select_fields_with_no_fields_specified(self):
        """测试未指定字段时返回所有数据"""
        test_data = pd.DataFrame(
            {
                "ts_code": ["600519.SH"],
                "total_revenue": [1000000000.0],
                "basic_eps": [10.5],
            }
        )

        # 不指定字段
        result = FieldSelector.select_fields(test_data, [])

        # 应该返回所有字段
        assert len(result) == 1
        assert set(result[0].keys()) == {"ts_code", "total_revenue", "basic_eps"}

    def test_select_fields_with_invalid_fields(self):
        """测试选择不存在的字段"""
        test_data = pd.DataFrame(
            {
                "ts_code": ["600519.SH"],
                "end_date": ["20240331"],
                "total_revenue": [1000000000.0],
            }
        )

        # 请求包含不存在字段的列表
        selected_fields = ["end_date", "total_revenue", "nonexistent_field"]
        result = FieldSelector.select_fields(test_data, selected_fields)

        # 应该只返回存在的字段
        assert len(result) == 1
        assert set(result[0].keys()) == {"end_date", "total_revenue"}

    def test_get_available_fields_from_dataframe(self):
        """测试从DataFrame获取可用字段"""
        test_data = pd.DataFrame(
            {
                "ts_code": ["600519.SH"],
                "end_date": ["20240331"],
                "total_revenue": [1000000000.0],
                "n_income_attr_p": [500000000.0],
                "basic_eps": [10.5],
            }
        )

        available_fields = FieldSelector.get_available_fields(test_data)

        expected_fields = [
            "ts_code",
            "end_date",
            "total_revenue",
            "n_income_attr_p",
            "basic_eps",
        ]
        assert set(available_fields) == set(expected_fields)

    def test_get_available_fields_from_list(self):
        """测试从列表数据获取可用字段"""
        test_data = [
            {
                "ts_code": "600519.SH",
                "end_date": "20240331",
                "total_revenue": 1000000000.0,
            },
            {
                "ts_code": "600519.SH",
                "end_date": "20231231",
                "total_revenue": 900000000.0,
                "extra_field": "extra",
            },
        ]

        available_fields = FieldSelector.get_available_fields(test_data)

        # 应该包含第一条记录的所有字段（extra_field在第二条记录中）
        expected_fields = ["ts_code", "end_date", "total_revenue"]
        assert set(available_fields) == set(expected_fields)

    def test_get_available_fields_from_empty_data(self):
        """测试从空数据获取可用字段"""
        empty_df = pd.DataFrame()

        available_fields = FieldSelector.get_available_fields(empty_df)

        # 应该返回空列表
        assert available_fields == []

    def test_field_selector_data_validation_methods(self):
        """测试数据验证的各种方法"""
        # 测试DataFrame
        empty_df = pd.DataFrame()
        non_empty_df = pd.DataFrame({"a": [1, 2, 3]})

        # 测试列表
        empty_list = []
        non_empty_list = [{"a": 1}]

        # 测试空值检查逻辑
        def is_data_empty(data):
            if hasattr(data, "empty") and data.empty:
                return True
            elif hasattr(data, "__len__") and len(data) == 0:
                return True
            else:
                return False

        # 验证各种数据类型
        assert is_data_empty(empty_df) == True
        assert is_data_empty(non_empty_df) == False
        assert is_data_empty(empty_list) == True
        assert is_data_empty(non_empty_list) == False

    def test_field_selector_handles_nan_values(self):
        """测试FieldSelector处理NaN值"""
        test_data = pd.DataFrame(
            {
                "ts_code": ["600519.SH", "600519.SH"],
                "end_date": ["20240331", None],
                "total_revenue": [1000000000.0, None],
                "basic_eps": [10.5, 9.8],
            }
        )

        result = FieldSelector.select_fields(
            test_data, ["end_date", "total_revenue", "basic_eps"]
        )

        # NaN在DataFrame转换为字典时会被转换为float('nan')
        import math

        assert len(result) == 2
        assert result[0]["end_date"] == "20240331"
        assert result[0]["total_revenue"] == 1000000000.0
        assert result[1]["end_date"] is None
        assert isinstance(result[1]["total_revenue"], float) and math.isnan(
            result[1]["total_revenue"]
        )

    def test_field_selector_duplicate_fields(self):
        """测试字段去重功能"""
        test_data = pd.DataFrame(
            {
                "ts_code": ["600519.SH"],
                "total_revenue": [1000000000.0],
                "basic_eps": [10.5],
            }
        )

        # 请求包含重复字段的列表
        selected_fields = ["total_revenue", "basic_eps", "total_revenue", "basic_eps"]
        result = FieldSelector.select_fields(test_data, selected_fields)

        # 结果应该不包含重复字段
        assert len(result) == 1
        assert set(result[0].keys()) == {"total_revenue", "basic_eps"}

    def test_field_selector_preserves_order(self):
        """测试字段顺序保持"""
        test_data = pd.DataFrame({"z_field": ["z"], "a_field": ["a"], "m_field": ["m"]})

        # 按特定顺序请求字段
        selected_fields = ["m_field", "a_field", "z_field"]
        result = FieldSelector.select_fields(test_data, selected_fields)

        # 验证字段顺序
        record = result[0]
        keys_order = list(record.keys())
        assert keys_order == ["m_field", "a_field", "z_field"]
