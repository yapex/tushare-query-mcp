"""
数据过滤器

处理财务数据的update_flag过滤逻辑。
"""

from typing import Any, Dict, List


def filter_by_update_flag(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    根据update_flag过滤重复记录

    业务逻辑：当同一股票同一报告期(end_date)有多条记录时，选择update_flag=1的记录

    Args:
        data: 原始数据列表

    Returns:
        过滤后的数据列表
    """
    # 检查数据是否为空（支持DataFrame和列表）
    if hasattr(data, "empty") and data.empty:
        # pandas DataFrame
        return []
    elif hasattr(data, "__len__") and len(data) == 0:
        # 列表或其他序列
        return []

    # 如果是DataFrame，先转换为字典列表
    if hasattr(data, "to_dict"):
        data = data.to_dict("records")

    # 按股票代码和报告期分组
    grouped = {}
    for record in data:
        ts_code = record.get("ts_code")
        end_date = record.get("end_date")

        if not ts_code or not end_date:
            continue

        key = f"{ts_code}_{end_date}"
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(record)

    # 对每组数据应用过滤规则
    result = []
    for key, records in grouped.items():
        if len(records) == 1:
            # 只有一条记录，直接使用
            result.append(records[0])
        else:
            # 多条记录，优先选择update_flag=1的记录
            preferred = [r for r in records if r.get("update_flag") == "1"]
            if preferred:
                result.append(preferred[0])
            else:
                # 没有update_flag=1的记录，选择第一条
                result.append(records[0])

    return result


# 导出主要接口
__all__ = [
    "filter_by_update_flag",
]
