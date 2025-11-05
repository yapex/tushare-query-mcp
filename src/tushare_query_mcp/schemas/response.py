"""
响应数据模型

定义所有API响应的数据模型，包括成功响应、错误响应和统一格式。
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator


class ResponseStatus(str, Enum):
    """响应状态枚举"""

    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"


class ErrorDetail(BaseModel):
    """错误详情模型"""

    code: str = Field(..., description="错误代码")
    message: str = Field(..., description="错误消息")
    field: Optional[str] = Field(None, description="错误字段")
    value: Optional[Any] = Field(None, description="错误值")

    class Config:
        """Pydantic 配置"""

        extra = "forbid"  # 禁止额外字段


class FinancialDataResponse(BaseModel):
    """基础财务数据响应模型"""

    # 状态信息
    status: ResponseStatus = Field(..., description="响应状态")
    message: str = Field(..., description="响应消息")

    # 数据内容
    data: List[Dict[str, Any]] = Field(default_factory=list, description="财务数据列表")
    total_records: int = Field(0, description="总记录数")

    # 元数据
    from_cache: bool = Field(False, description="是否来自缓存")
    query_time: float = Field(0.0, description="查询耗时（秒）")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间戳")

    # 可选的错误详情
    error: Optional[ErrorDetail] = Field(None, description="错误详情")

    @validator("total_records")
    def validate_total_records(cls, v, values):
        """验证总记录数与数据长度一致性"""
        if "data" in values and isinstance(values["data"], list):
            data_length = len(values["data"])
            if v != data_length:
                # 如果不一致，使用实际数据长度
                return data_length
        return v

    @validator("query_time")
    def validate_query_time(cls, v):
        """验证查询时间"""
        if v < 0:
            raise ValueError("查询时间不能为负数")
        return v

    class Config:
        """Pydantic 配置"""

        use_enum_values = True  # 使用枚举值
        json_encoders = {datetime: lambda v: v.isoformat()}  # 日期时间序列化


class IncomeResponse(FinancialDataResponse):
    """利润表响应模型"""

    # 利润表特有字段（如果有的话）
    data_type: str = Field("income", description="数据类型")

    # 可以添加利润表特有的元数据
    report_types: Optional[List[str]] = Field(None, description="包含的报告类型")


class BalanceResponse(FinancialDataResponse):
    """资产负债表响应模型"""

    # 资产负债表特有字段
    data_type: str = Field("balance", description="数据类型")


class CashFlowResponse(FinancialDataResponse):
    """现金流量表响应模型"""

    # 现金流量表特有字段
    data_type: str = Field("cashflow", description="数据类型")


class StockResponse(FinancialDataResponse):
    """股票基本信息响应模型"""

    # 股票信息特有字段
    data_type: str = Field("stock", description="数据类型")


class HealthCheckResponse(BaseModel):
    """健康检查响应模型"""

    status: str = Field(..., description="服务状态")
    message: str = Field(..., description="状态消息")
    timestamp: datetime = Field(default_factory=datetime.now, description="检查时间")

    # 服务信息
    version: str = Field(..., description="服务版本")
    uptime: float = Field(..., description="运行时间（秒）")

    # 组件状态
    database: str = Field(..., description="数据库状态")
    cache: str = Field(..., description="缓存状态")
    tushare_api: str = Field(..., description="Tushare API状态")


class CacheStatsResponse(BaseModel):
    """缓存统计响应模型"""

    status: str = Field(..., description="查询状态")
    message: str = Field(..., description="状态消息")

    # 缓存统计信息
    cache_size: int = Field(..., description="缓存大小（条目数）")
    cache_memory: str = Field(..., description="缓存内存使用")
    hit_rate: float = Field(..., description="命中率")
    miss_rate: float = Field(..., description="未命中率")

    # 各类型缓存统计
    income_cache: Dict[str, Any] = Field(..., description="利润表缓存统计")
    balance_cache: Dict[str, Any] = Field(..., description="资产负债表缓存统计")
    cashflow_cache: Dict[str, Any] = Field(..., description="现金流量表缓存统计")
    stock_cache: Dict[str, Any] = Field(..., description="股票信息缓存统计")

    timestamp: datetime = Field(default_factory=datetime.now, description="统计时间")


class CacheClearResponse(BaseModel):
    """缓存清理响应模型"""

    status: str = Field(..., description="清理状态")
    message: str = Field(..., description="清理消息")

    # 清理结果
    cleared_count: int = Field(..., description="清理的缓存条目数")
    cleared_types: List[str] = Field(..., description="清理的缓存类型")

    timestamp: datetime = Field(default_factory=datetime.now, description="清理时间")


# 工具函数
def create_success_response(
    data: List[Dict[str, Any]],
    message: str = "查询成功",
    from_cache: bool = False,
    query_time: float = 0.0,
    **kwargs,
) -> FinancialDataResponse:
    """创建成功响应"""
    return FinancialDataResponse(
        status=ResponseStatus.SUCCESS,
        message=message,
        data=data,
        total_records=len(data),
        from_cache=from_cache,
        query_time=query_time,
        **kwargs,
    )


def create_error_response(
    message: str,
    error_code: str = "UNKNOWN_ERROR",
    error_field: Optional[str] = None,
    error_value: Optional[Any] = None,
    query_time: float = 0.0,
    **kwargs,
) -> FinancialDataResponse:
    """创建错误响应"""
    return FinancialDataResponse(
        status=ResponseStatus.ERROR,
        message=message,
        data=[],
        total_records=0,
        from_cache=False,
        query_time=query_time,
        error=ErrorDetail(
            code=error_code, message=message, field=error_field, value=error_value
        ),
        **kwargs,
    )


def create_income_response(
    data: List[Dict[str, Any]], message: str = "利润表查询成功", **kwargs
) -> IncomeResponse:
    """创建利润表响应"""
    return IncomeResponse(
        status=ResponseStatus.SUCCESS,
        message=message,
        data=data,
        total_records=len(data),
        data_type="income",
        **kwargs,
    )


def create_balance_response(
    data: List[Dict[str, Any]], message: str = "资产负债表查询成功", **kwargs
) -> BalanceResponse:
    """创建资产负债表响应"""
    return BalanceResponse(
        status=ResponseStatus.SUCCESS,
        message=message,
        data=data,
        total_records=len(data),
        data_type="balance",
        **kwargs,
    )


def create_cashflow_response(
    data: List[Dict[str, Any]], message: str = "现金流量表查询成功", **kwargs
) -> CashFlowResponse:
    """创建现金流量表响应"""
    return CashFlowResponse(
        status=ResponseStatus.SUCCESS,
        message=message,
        data=data,
        total_records=len(data),
        data_type="cashflow",
        **kwargs,
    )


def create_stock_response(
    data: List[Dict[str, Any]], message: str = "股票信息查询成功", **kwargs
) -> StockResponse:
    """创建股票信息响应"""
    return StockResponse(
        status=ResponseStatus.SUCCESS,
        message=message,
        data=data,
        total_records=len(data),
        data_type="stock",
        **kwargs,
    )


# 导出所有响应模型
__all__ = [
    "ResponseStatus",
    "ErrorDetail",
    "FinancialDataResponse",
    "IncomeResponse",
    "BalanceResponse",
    "CashFlowResponse",
    "StockResponse",
    "HealthCheckResponse",
    "CacheStatsResponse",
    "CacheClearResponse",
    # 工具函数
    "create_success_response",
    "create_error_response",
    "create_income_response",
    "create_balance_response",
    "create_cashflow_response",
    "create_stock_response",
]
