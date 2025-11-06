"""
字段选择器测试用例
测试从完整财务数据中选择指定字段的功能
"""

from typing import Any, Dict, List

import pytest

# 导入待测试的模块
from tushare_query_mcp.utils.field_selector import FieldSelector


class TestFieldSelector:
    """测试字段选择器"""

    @pytest.fixture
    def sample_income_data(self):
        """示例利润表完整数据"""
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
                "basic_eps": 14.78,
                "diluted_eps": 14.78,
                "total_revenue": 81934176144.84,
                "revenue": 81934176144.84,
                "n_income_attr_p": 18555488059.34,
                "total_profit": 22605188059.34,
                "income_tax": 4049700000.00,
                "n_income": 18555488059.34,
                "ebit": 22605188059.34,
                "ebitda": 22605188059.34,
                "update_flag": "1",
            },
        ]

    @pytest.fixture
    def sample_balance_data(self):
        """示例资产负债表完整数据"""
        return [
            {
                "ts_code": "600519.SH",
                "ann_date": "20241030",
                "f_ann_date": "20241030",
                "end_date": "20240930",
                "report_type": "1",
                "comp_type": "1",
                "end_type": "4",
                "total_assets": 2000000000000.00,
                "total_liab": 500000000000.00,
                "money_cap": 100000000000.00,
                "total_cur_assets": 1500000000000.00,
                "total_cur_liab": 300000000000.00,
                "intangible_assets": 50000000000.00,
                "goodwill": 10000000000.00,
                "update_flag": "1",
            }
        ]

    def test_select_fields_single_record(self, sample_income_data):
        """测试单条记录的字段选择"""
        data = [sample_income_data[0]]  # 只取第一条记录
        fields = ["ts_code", "end_date", "n_income_attr_p", "revenue"]

        result = FieldSelector.select_fields(data, fields)

        assert len(result) == 1
        selected = result[0]

        # 验证只包含指定字段
        assert set(selected.keys()) == {
            "ts_code",
            "end_date",
            "n_income_attr_p",
            "revenue",
        }
        assert selected["ts_code"] == "600519.SH"
        assert selected["end_date"] == "20240930"
        assert selected["n_income_attr_p"] == 19223784414.08
        assert selected["revenue"] == 120714458386.98

    def test_select_fields_multiple_records(self, sample_income_data):
        """测试多条记录的字段选择"""
        fields = ["ts_code", "end_date", "basic_eps"]

        result = FieldSelector.select_fields(sample_income_data, fields)

        assert len(result) == 2

        # 验证每条记录都只包含指定字段
        for record in result:
            assert set(record.keys()) == {"ts_code", "end_date", "basic_eps"}

        assert result[0]["basic_eps"] == 15.33
        assert result[1]["basic_eps"] == 14.78

    def test_select_fields_all_fields(self, sample_income_data):
        """测试选择所有字段"""
        # 获取所有字段
        all_fields = list(sample_income_data[0].keys())

        result = FieldSelector.select_fields(sample_income_data, all_fields)

        assert len(result) == 2
        # 验证字段数量和内容不变
        for record in result:
            assert len(record) == len(all_fields)
            assert set(record.keys()) == set(all_fields)

    def test_select_fields_nonexistent_field(self, sample_income_data):
        """测试选择不存在的字段"""
        fields = ["ts_code", "end_date", "nonexistent_field", "another_invalid"]

        result = FieldSelector.select_fields(sample_income_data, fields)

        assert len(result) == 2

        # 验证只返回存在的字段
        for record in result:
            assert set(record.keys()) == {"ts_code", "end_date"}
            assert "nonexistent_field" not in record
            assert "another_invalid" not in record

    def test_select_fields_mixed_valid_invalid(self, sample_income_data):
        """测试混合有效和无效字段"""
        fields = [
            "ts_code",
            "invalid_field",
            "n_income_attr_p",
            "another_invalid",
            "basic_eps",
        ]

        result = FieldSelector.select_fields(sample_income_data, fields)

        assert len(result) == 2

        # 验证只返回存在的字段
        for record in result:
            assert set(record.keys()) == {"ts_code", "n_income_attr_p", "basic_eps"}

    def test_select_fields_empty_fields_list(self, sample_income_data):
        """测试空字段列表"""
        result = FieldSelector.select_fields(sample_income_data, [])

        # 应该返回所有字段的记录（空fields表示返回所有字段）
        assert len(result) == 2
        # 验证返回的数据与原始数据相同
        assert result == sample_income_data  # 应该返回原始数据的所有字段

    def test_select_fields_empty_data(self):
        """测试空数据"""
        result = FieldSelector.select_fields([], ["ts_code", "end_date"])
        assert result == []

    def test_select_fields_duplicate_fields(self, sample_income_data):
        """测试重复字段列表"""
        fields = ["ts_code", "end_date", "ts_code", "n_income_attr_p", "end_date"]

        result = FieldSelector.select_fields(sample_income_data, fields)

        assert len(result) == 2

        # 验证重复字段被去重
        for record in result:
            assert set(record.keys()) == {"ts_code", "end_date", "n_income_attr_p"}

    def test_select_fields_with_none_values(self):
        """测试包含None值的数据"""
        data = [
            {
                "ts_code": "600519.SH",
                "end_date": "20240930",
                "n_income_attr_p": 19223784414.08,
                "revenue": None,  # None值
                "basic_eps": 15.33,
                "invalid_field": None,  # None值但字段有效
            }
        ]

        result = FieldSelector.select_fields(
            data, ["ts_code", "end_date", "revenue", "invalid_field"]
        )

        assert len(result) == 1
        selected = result[0]

        # 验证None值被保留（字段选择器不过滤值，只过滤字段）
        assert selected["revenue"] is None
        assert selected["invalid_field"] is None

    def test_select_fields_numeric_types(self, sample_income_data):
        """测试不同数值类型的字段选择"""
        fields = ["basic_eps", "total_revenue", "n_income_attr_p"]

        result = FieldSelector.select_fields(sample_income_data, fields)

        assert len(result) == 2

        # 验证数值类型被正确保留
        for record in result:
            assert isinstance(record["basic_eps"], (int, float))
            assert isinstance(record["total_revenue"], (int, float))
            assert isinstance(record["n_income_attr_p"], (int, float))

    def test_select_fields_string_types(self, sample_income_data):
        """测试字符串类型的字段选择"""
        fields = ["ts_code", "end_date", "report_type"]

        result = FieldSelector.select_fields(sample_income_data, fields)

        assert len(result) == 2

        # 验证字符串类型被正确保留
        for record in result:
            assert isinstance(record["ts_code"], str)
            assert isinstance(record["end_date"], str)
            assert isinstance(record["report_type"], str)

    def test_select_fields_performance_large_dataset(self):
        """测试大数据集的性能"""
        # 创建大数据集
        large_data = []
        for i in range(1000):
            large_data.append(
                {
                    "ts_code": f"60000{i % 10}.SH",
                    "end_date": "20240930",
                    "basic_eps": 10.0 + i,
                    "n_income_attr_p": 1000000000.0 + i * 1000000,
                    "revenue": 10000000000.0 + i * 10000000,
                    f"extra_field_{i}": f"value_{i}",  # 每条记录都有不同的额外字段
                }
            )

        # 只选择几个核心字段
        fields = ["ts_code", "end_date", "basic_eps"]

        import time

        start_time = time.time()

        result = FieldSelector.select_fields(large_data, fields)

        end_time = time.time()
        processing_time = end_time - start_time

        # 验证结果
        assert len(result) == 1000
        for record in result:
            assert set(record.keys()) == {"ts_code", "end_date", "basic_eps"}

        # 验证性能（应该在合理时间内完成）
        assert processing_time < 1.0, f"字段选择耗时过长: {processing_time:.3f}秒"

    def test_get_available_fields(self, sample_income_data):
        """测试获取可用字段列表"""
        fields = FieldSelector.get_available_fields(sample_income_data)

        # 验证返回所有字段的列表
        assert isinstance(fields, list)
        assert len(fields) > 10  # 应该有多个字段

        # 验证包含已知字段
        assert "ts_code" in fields
        assert "end_date" in fields
        assert "basic_eps" in fields
        assert "n_income_attr_p" in fields

    def test_get_available_fields_empty_data(self):
        """测试空数据的可用字段获取"""
        fields = FieldSelector.get_available_fields([])
        assert fields == []

    def test_get_available_fields_different_data_types(
        self, sample_income_data, sample_balance_data
    ):
        """测试不同数据类型的可用字段"""
        income_fields = FieldSelector.get_available_fields(sample_income_data)
        balance_fields = FieldSelector.get_available_fields(sample_balance_data)

        # 验证两种数据类型的字段不同
        assert set(income_fields) != set(balance_fields)

        # 验证都包含基础字段
        assert "ts_code" in income_fields
        assert "ts_code" in balance_fields

    def test_validate_fields_exist(self, sample_income_data):
        """测试验证字段是否存在"""
        # 测试存在的字段
        valid_fields = ["ts_code", "end_date", "basic_eps"]
        missing_fields = FieldSelector.validate_fields(sample_income_data, valid_fields)
        assert missing_fields == []

        # 测试不存在的字段
        mixed_fields = ["ts_code", "end_date", "invalid_field", "another_invalid"]
        missing_fields = FieldSelector.validate_fields(sample_income_data, mixed_fields)
        assert set(missing_fields) == {"invalid_field", "another_invalid"}

    def test_validate_fields_empty_data(self):
        """测试空数据的字段验证"""
        missing_fields = FieldSelector.validate_fields([], ["ts_code", "end_date"])
        assert missing_fields == ["ts_code", "end_date"]


class TestFieldSelectorEdgeCases:
    """测试字段选择器的边界情况"""

    def test_select_fields_with_nested_data(self):
        """测试包含嵌套数据结构"""
        data = [
            {
                "ts_code": "600519.SH",
                "end_date": "20240930",
                "simple_field": "value",
                "nested_data": {"inner_field": "inner_value", "number": 123},
                "list_field": [1, 2, 3],
            }
        ]

        result = FieldSelector.select_fields(
            data, ["ts_code", "simple_field", "nested_data"]
        )

        assert len(result) == 1
        selected = result[0]

        # 验证嵌套结构被完整保留
        assert selected["nested_data"] == {"inner_field": "inner_value", "number": 123}

    def test_select_fields_with_special_characters(self):
        """测试包含特殊字符的字段名"""
        data = [
            {
                "ts_code": "600519.SH",
                "field-with-dash": "value1",
                "field_with_underscore": "value2",
                "field.with.dots": "value3",
                "field with spaces": "value4",
            }
        ]

        fields = ["ts_code", "field-with-dash", "field_with_underscore"]
        result = FieldSelector.select_fields(data, fields)

        assert len(result) == 1
        selected = result[0]

        assert selected["field-with-dash"] == "value1"
        assert selected["field_with_underscore"] == "value2"
        assert "field.with.dots" not in selected

    def test_select_fields_case_sensitivity(self):
        """测试字段名大小写敏感性"""
        data = [
            {
                "ts_code": "600519.SH",
                "TS_CODE": "different_value",
                "End_Date": "20240930",
                "end_date": "20240930",
            }
        ]

        # 测试精确匹配（大小写敏感）
        result = FieldSelector.select_fields(data, ["ts_code", "end_date"])
        assert len(result) == 1
        selected = result[0]
        assert selected["ts_code"] == "600519.SH"
        assert selected["end_date"] == "20240930"
        assert "TS_CODE" not in selected
        assert "End_Date" not in selected


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
