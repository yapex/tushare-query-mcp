"""
字段选择器

从完整的财务数据中选择用户指定的字段，实现智能字段返回功能。
"""

import logging
from typing import Any, Dict, List, Set, Tuple, Type, Union

logger = logging.getLogger(__name__)


class FieldSelector:
    """字段选择器"""

    @staticmethod
    def select_fields(
        data: List[Dict[str, Any]], fields: List[str]
    ) -> List[Dict[str, Any]]:
        """
        从数据中选择指定字段

        Args:
            data: 原始数据列表
            fields: 要选择的字段列表

        Returns:
            只包含指定字段的数据列表
        """
        # 检查数据是否为空（支持DataFrame和列表）
        if hasattr(data, "empty") and data.empty:
            # pandas DataFrame
            return []
        elif hasattr(data, "__len__") and len(data) == 0:
            # 列表或其他序列
            return []

        # 如果没有指定字段，返回所有字段
        if not fields:
            # 如果是DataFrame，先转换为字典列表
            if hasattr(data, "to_dict"):
                return data.to_dict("records")
            # 返回所有记录的所有字段
            return data.copy()

        # 去重字段列表，保持顺序
        seen_fields = set()
        unique_fields = []
        for field in fields:
            if field not in seen_fields:
                seen_fields.add(field)
                unique_fields.append(field)

        # 获取第一条记录的所有可用字段
        if hasattr(data, "empty") and data.empty:
            available_fields = set()
        elif hasattr(data, "__len__") and len(data) > 0:
            # DataFrame转换为字典列表后再获取字段
            if hasattr(data, "to_dict"):
                data_dict = data.to_dict("records")
                if data_dict:
                    available_fields = set(data_dict[0].keys())
                else:
                    available_fields = set()
            else:
                available_fields = set(data[0].keys())
        else:
            available_fields = set()

        # 过滤出存在的字段
        valid_fields = [field for field in unique_fields if field in available_fields]

        if not valid_fields:
            logger.warning("没有找到任何有效字段")
            # 如果是DataFrame，先转换为字典列表
            if hasattr(data, "to_dict"):
                data = data.to_dict("records")
            return [{} for _ in data]

        # 为每条记录选择字段
        result = []

        # 如果是DataFrame，先转换为字典列表
        if hasattr(data, "to_dict"):
            data = data.to_dict("records")

        for record in data:
            selected_record = {
                field: record[field] for field in valid_fields if field in record
            }
            result.append(selected_record)

        logger.debug(
            f"字段选择完成: 从 {len(data[0]) if data else 0} 个字段中选择了 {len(valid_fields)} 个字段"
        )
        return result

    @staticmethod
    def get_available_fields(data: List[Dict[str, Any]]) -> List[str]:
        """
        获取数据中所有可用字段的列表

        Args:
            data: 数据列表

        Returns:
            所有可用字段的列表
        """
        # 检查数据是否为空（支持DataFrame和列表）
        if hasattr(data, "empty") and data.empty:
            return []
        elif hasattr(data, "__len__") and len(data) == 0:
            return []

        # 获取第一条记录的所有字段
        if hasattr(data, "to_dict"):
            # DataFrame转换为字典列表
            data_dict = data.to_dict("records")
            if data_dict:
                fields = list(data_dict[0].keys())
            else:
                fields = []
        else:
            fields = list(data[0].keys())
        return fields

    @staticmethod
    def validate_fields(data: List[Dict[str, Any]], fields: List[str]) -> List[str]:
        """
        验证字段在数据中是否存在

        Args:
            data: 数据列表
            fields: 要验证的字段列表

        Returns:
            不存在的字段列表
        """
        if not data:
            return fields.copy()

        available_fields = set(data[0].keys())
        missing_fields = [field for field in fields if field not in available_fields]

        if missing_fields:
            logger.warning(f"以下字段在数据中不存在: {missing_fields}")

        return missing_fields

    @staticmethod
    def select_common_fields(
        data: List[Dict[str, Any]], min_occurrence: int = 1
    ) -> List[str]:
        """
        选择在多条记录中都存在的字段

        Args:
            data: 数据列表
            min_occurrence: 字段出现的最小次数（默认为1，即所有记录中都存在的字段）

        Returns:
            共同字段的列表
        """
        if not data:
            return []

        # 统计每个字段的出现次数
        field_counts = {}
        for record in data:
            for field in record.keys():
                field_counts[field] = field_counts.get(field, 0) + 1

        # 筛选出出现次数足够的字段
        common_fields = [
            field for field, count in field_counts.items() if count >= min_occurrence
        ]

        logger.debug(
            f"找到 {len(common_fields)} 个共同字段（最少出现 {min_occurrence} 次）"
        )
        return common_fields

    @staticmethod
    def merge_field_selections(
        data: List[Dict[str, Any]], field_groups: List[List[str]]
    ) -> List[Dict[str, Any]]:
        """
        合并多个字段选择的结果

        Args:
            data: 原始数据列表
            field_groups: 字段组列表

        Returns:
            合并后的数据列表
        """
        if not data or not field_groups:
            return data.copy()

        # 合并所有字段组并去重
        all_fields = []
        seen_fields = set()
        for field_group in field_groups:
            for field in field_group:
                if field not in seen_fields:
                    seen_fields.add(field)
                    all_fields.append(field)

        return FieldSelector.select_fields(data, all_fields)


# 便捷函数
def select_fields(
    data: List[Dict[str, Any]], fields: List[str]
) -> List[Dict[str, Any]]:
    """便捷的字段选择函数"""
    return FieldSelector.select_fields(data, fields)


def get_available_fields(data: List[Dict[str, Any]]) -> List[str]:
    """便捷的获取可用字段函数"""
    return FieldSelector.get_available_fields(data)


# 导出主要接口
__all__ = [
    "FieldSelector",
    "select_fields",
    "get_available_fields",
]
