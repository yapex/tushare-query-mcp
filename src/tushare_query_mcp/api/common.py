"""
API通用模块
提供所有API路由的公共组件：模型、验证函数、依赖注入等
"""

import os
import sys
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Generic, List, Optional, Type, TypeVar

from fastapi import Depends, HTTPException
from pydantic import BaseModel, Field

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from ..config import get_settings

# 泛型类型变量
T = TypeVar("T", bound="BaseFinancialService")


# API响应模型
class APIResponse(BaseModel):
    """标准API响应格式"""

    status: str = Field(..., description="响应状态：success/error")
    data: List[dict] = Field(default=[], description="数据列表")
    total_records: int = Field(default=0, description="总记录数")
    message: str = Field(..., description="响应消息")
    from_cache: bool = Field(default=False, description="是否来自缓存")
    query_time: float = Field(..., description="查询耗时（秒）")
    error: Optional[str] = Field(default=None, description="错误信息（如果有）")
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(), description="响应时间戳"
    )


class HealthResponse(BaseModel):
    """健康检查响应"""

    status: str = Field(..., description="服务状态：healthy/unhealthy")
    message: str = Field(..., description="状态消息")
    data_source: str = Field(..., description="数据源状态")
    timestamp: float = Field(..., description="时间戳")


class FieldsResponse(BaseModel):
    """字段列表响应"""

    status: str = Field(default="success", description="响应状态")
    data: List[str] = Field(..., description="字段列表")
    total_count: int = Field(..., description="字段总数")
    message: str = Field(..., description="响应消息")
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(), description="响应时间戳"
    )


class ValidationResponse(BaseModel):
    """字段验证响应"""

    status: str = Field(default="success", description="响应状态")
    data: dict = Field(..., description="验证结果")
    message: str = Field(default="字段验证完成", description="响应消息")
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(), description="响应时间戳"
    )


# 验证工具函数
def validate_date_format(date_str: str) -> bool:
    """验证日期格式 YYYYMMDD"""
    try:
        datetime.strptime(date_str, "%Y%m%d")
        return True
    except ValueError:
        return False


def validate_date_range(start_date: str, end_date: str) -> bool:
    """验证日期范围有效性"""
    if not (validate_date_format(start_date) and validate_date_format(end_date)):
        return False

    start_dt = datetime.strptime(start_date, "%Y%m%d")
    end_dt = datetime.strptime(end_date, "%Y%m%d")
    return start_dt <= end_dt


def validate_ts_code(ts_code: str) -> bool:
    """验证股票代码格式"""
    return len(ts_code) >= 6 and "." in ts_code


def parse_fields(fields_str: str) -> List[str]:
    """解析字段字符串"""
    if not fields_str:
        raise HTTPException(status_code=422, detail="字段列表不能为空")

    field_list = [field.strip() for field in fields_str.split(",") if field.strip()]
    if not field_list:
        raise HTTPException(status_code=422, detail="字段列表格式无效")

    if len(field_list) > 50:
        raise HTTPException(status_code=400, detail="字段数量不能超过50个")

    return field_list


def validate_common_params(
    ts_code: str,
    fields: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    """验证公共参数"""
    # 验证股票代码
    if not ts_code:
        raise HTTPException(status_code=422, detail="股票代码不能为空")

    if not validate_ts_code(ts_code):
        raise HTTPException(
            status_code=422,
            detail="股票代码格式无效，应为：代码.交易所（如：600519.SH）",
        )

    # 解析和验证字段
    field_list = parse_fields(fields)

    # 验证日期格式
    if start_date and not validate_date_format(start_date):
        raise HTTPException(
            status_code=422, detail="开始日期格式无效，应为YYYYMMDD（如：20240101）"
        )

    if end_date and not validate_date_format(end_date):
        raise HTTPException(
            status_code=422, detail="结束日期格式无效，应为YYYYMMDD（如：20241231）"
        )

    # 验证日期范围
    if start_date and end_date and not validate_date_range(start_date, end_date):
        raise HTTPException(status_code=400, detail="结束日期不能早于开始日期")

    return field_list


def validate_report_type(report_type: Optional[str]) -> None:
    """验证报告类型"""
    if report_type and report_type not in ["1", "2"]:
        raise HTTPException(
            status_code=422, detail="报告类型无效，应为：1-合并报表，2-母公司报表"
        )


# 抽象基类定义
class BaseFinancialService(ABC):
    """财务服务抽象基类"""

    @abstractmethod
    async def get_data(self, request):
        """获取数据"""
        pass

    @abstractmethod
    async def health_check(self) -> dict:
        """健康检查"""
        pass

    @abstractmethod
    async def get_available_fields(
        self,
        ts_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[str]:
        """获取可用字段"""
        pass

    @abstractmethod
    async def validate_fields(
        self,
        ts_code: str,
        fields: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> dict:
        """验证字段"""
        pass


# 通用依赖注入工厂
def create_service_dependency(service_class: Type[T]):
    """创建服务依赖注入函数"""

    def get_service() -> T:
        """获取服务实例"""
        settings = get_settings()
        return service_class(settings.tushare_token)

    return get_service


# 通用API响应转换函数
def create_api_response(service_response) -> APIResponse:
    """将Service响应转换为API响应"""
    return APIResponse(
        status=service_response.status.value,
        data=service_response.data,
        total_records=service_response.total_records,
        message=service_response.message,
        from_cache=service_response.from_cache,
        query_time=service_response.query_time,
        error=service_response.error,
    )


def create_health_response(health_status: dict) -> HealthResponse:
    """创建健康检查响应"""
    return HealthResponse(
        status=health_status.get("status", "unknown"),
        message=health_status.get("message", "状态未知"),
        data_source=health_status.get("data_source", "unknown"),
        timestamp=health_status.get("timestamp", datetime.now().timestamp()),
    )


def create_fields_response(fields: List[str]) -> FieldsResponse:
    """创建字段列表响应"""
    return FieldsResponse(
        data=fields, total_count=len(fields), message=f"获取到 {len(fields)} 个可用字段"
    )


def create_validation_response(validation_result: dict) -> ValidationResponse:
    """创建字段验证响应"""
    return ValidationResponse(data=validation_result)


# 导出所有公共组件
__all__ = [
    "APIResponse",
    "HealthResponse",
    "FieldsResponse",
    "ValidationResponse",
    "validate_date_format",
    "validate_date_range",
    "validate_ts_code",
    "parse_fields",
    "validate_common_params",
    "validate_report_type",
    "BaseFinancialService",
    "create_service_dependency",
    "create_api_response",
    "create_health_response",
    "create_fields_response",
    "create_validation_response",
]
