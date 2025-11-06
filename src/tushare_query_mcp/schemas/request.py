"""
请求数据模型

定义所有API请求的数据模型，包括参数验证、字段选择等功能。
"""

import re
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, validator


class FinancialDataRequest(BaseModel):
    """基础财务数据请求模型（Service层使用）"""

    # 必填字段
    ts_code: str = Field(..., description="股票代码，如 600519.SH")
    fields: List[str] = Field(default=[], description="需要返回的字段列表")

    # 可选字段
    start_date: Optional[str] = Field(None, description="开始日期，格式 YYYYMMDD")
    end_date: Optional[str] = Field(None, description="结束日期，格式 YYYYMMDD")

    @validator("ts_code")
    def validate_ts_code(cls, v):
        """验证股票代码格式"""
        if not v or not v.strip():
            raise ValueError("股票代码不能为空")

        v = v.strip().upper()

        # 验证股票代码格式：6位数字.交易所
        pattern = r"^\d{6}\.(SH|SZ|BJ)$"
        if not re.match(pattern, v):
            raise ValueError("股票代码格式错误，应为: 6位数字.交易所，如 600519.SH")

        return v

    @validator("fields")
    def validate_fields(cls, v):
        """验证字段列表"""
        if not v:
            return []  # 允许空字段列表

        # 过滤空字段并保持顺序，只去除重复的连续字段
        cleaned_fields = []
        seen = set()
        for field in v:
            field = field.strip()
            if field and field not in seen:
                cleaned_fields.append(field)
                seen.add(field)

        return cleaned_fields  # 可能为空列表

    @validator("start_date", "end_date")
    def validate_date_format(cls, v):
        """验证日期格式"""
        if v is None:
            return v

        if not v or not v.strip():
            return None

        v = v.strip()

        # 验证日期格式：YYYYMMDD
        pattern = r"^\d{8}$"
        if not re.match(pattern, v):
            raise ValueError("日期格式错误，应为 YYYYMMDD，如 20240101")

        # 验证日期是否有效
        try:
            datetime.strptime(v, "%Y%m%d")
        except ValueError:
            raise ValueError(f"无效的日期: {v}")

        return v

    @validator("end_date")
    def validate_date_range(cls, v, values):
        """验证日期范围：结束日期不能早于开始日期"""
        if v is None or "start_date" not in values or values["start_date"] is None:
            return v

        start_date = values["start_date"]

        if start_date and v < start_date:
            raise ValueError("结束日期不能早于开始日期")

        return v


class DataSourceRequest(BaseModel):
    """数据源请求模型（TushareDataSource层使用）"""

    # 必填字段
    ts_code: str = Field(..., description="股票代码，如 600519.SH")

    # 可选字段
    start_date: Optional[str] = Field(None, description="开始日期，格式 YYYYMMDD")
    end_date: Optional[str] = Field(None, description="结束日期，格式 YYYYMMDD")

    # 注意：DataSourceRequest不接受fields参数，因为它总是返回所有字段

    @validator("ts_code")
    def validate_ts_code(cls, v):
        """验证股票代码格式"""
        if not v or not v.strip():
            raise ValueError("股票代码不能为空")

        v = v.strip().upper()

        # 验证股票代码格式：6位数字.交易所
        pattern = r"^\d{6}\.(SH|SZ|BJ)$"
        if not re.match(pattern, v):
            raise ValueError("股票代码格式错误，应为: 6位数字.交易所，如 600519.SH")

        return v

    @validator("start_date", "end_date")
    def validate_date_format(cls, v):
        """验证日期格式"""
        if v is None:
            return v

        if not v or not v.strip():
            return None

        v = v.strip()

        # 验证日期格式：YYYYMMDD
        pattern = r"^\d{8}$"
        if not re.match(pattern, v):
            raise ValueError("日期格式错误，应为 YYYYMMDD，如 20240101")

        # 验证日期是否有效
        try:
            datetime.strptime(v, "%Y%m%d")
        except ValueError:
            raise ValueError(f"无效的日期: {v}")

        return v

    @validator("end_date")
    def validate_date_range(cls, v, values):
        """验证日期范围：结束日期不能早于开始日期"""
        if v is None or "start_date" not in values or values["start_date"] is None:
            return v

        start_date = values["start_date"]

        if start_date and v < start_date:
            raise ValueError("结束日期不能早于开始日期")

        return v


class IncomeRequest(FinancialDataRequest):
    """利润表数据请求模型（Service层使用）"""

    # 利润表特有字段
    report_type: Optional[str] = Field(None, description="报告类型")
    period: Optional[str] = Field(None, description="报告期")

    @validator("report_type")
    def validate_report_type(cls, v):
        """验证报告类型"""
        if v is None:
            return v

        valid_types = ["1", "2", "3", "4", "合并报表", "单季合并", "调整单季合并表"]
        if v not in valid_types:
            raise ValueError(f"无效的报告类型: {v}")

        return v


class BalanceRequest(FinancialDataRequest):
    """资产负债表数据请求模型（Service层使用）"""

    pass


class CashFlowRequest(FinancialDataRequest):
    """现金流量表数据请求模型（Service层使用）"""

    pass


class StockRequest(FinancialDataRequest):
    """股票基本信息请求模型（Service层使用）"""

    # 股票信息通常不需要日期范围
    start_date: Optional[str] = None
    end_date: Optional[str] = None


# 数据源层请求模型（不包含fields参数）
class IncomeDataSourceRequest(DataSourceRequest):
    """利润表数据源请求模型（TushareDataSource层使用）"""

    pass


class BalanceDataSourceRequest(DataSourceRequest):
    """资产负债表数据源请求模型（TushareDataSource层使用）"""

    pass


class CashFlowDataSourceRequest(DataSourceRequest):
    """现金流量表数据源请求模型（TushareDataSource层使用）"""

    pass


class StockDataSourceRequest(DataSourceRequest):
    """股票基本信息数据源请求模型（TushareDataSource层使用）"""

    # 股票信息通常不需要日期范围
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class HealthCheckRequest(BaseModel):
    """健康检查请求模型"""

    # 健康检查通常不需要参数
    pass


class CacheStatsRequest(BaseModel):
    """缓存统计请求模型"""

    # 缓存统计通常不需要参数
    pass


class CacheClearRequest(BaseModel):
    """缓存清理请求模型"""

    # 可以指定要清理的缓存类型
    cache_type: Optional[str] = Field("all", description="要清理的缓存类型")

    @validator("cache_type")
    def validate_cache_type(cls, v):
        """验证缓存类型"""
        valid_types = ["all", "income", "balance", "cashflow", "stock"]
        if v not in valid_types:
            raise ValueError(f"无效的缓存类型: {v}")

        return v


# 导出所有请求模型
__all__ = [
    # Service层请求模型（包含fields参数）
    "FinancialDataRequest",
    "IncomeRequest",
    "BalanceRequest",
    "CashFlowRequest",
    "StockRequest",
    # 数据源层请求模型（不包含fields参数）
    "DataSourceRequest",
    "IncomeDataSourceRequest",
    "BalanceDataSourceRequest",
    "CashFlowDataSourceRequest",
    "StockDataSourceRequest",
    # 其他请求模型
    "HealthCheckRequest",
    "CacheStatsRequest",
    "CacheClearRequest",
]
