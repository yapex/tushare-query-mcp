"""
API路由基类
提供通用的API路由逻辑，减少重复代码
"""

from datetime import datetime
from typing import Generic, List, Optional, Type, TypeVar

from fastapi import APIRouter, Depends, HTTPException, Query

from .common import (APIResponse, FieldsResponse, HealthResponse,
                     ValidationResponse, create_api_response,
                     create_fields_response, create_health_response,
                     create_service_dependency, create_validation_response,
                     validate_common_params)

# 泛型类型变量
T = TypeVar("T")
RequestType = TypeVar("RequestType")


class BaseFinancialRoutes(Generic[T, RequestType]):
    """财务数据API路由基类"""

    def __init__(
        self,
        service_class: Type[T],
        request_class: Type[RequestType],
        router_prefix: str,
        tag: str,
        description: str,
    ):
        """
        初始化基础路由

        Args:
            service_class: 服务类
            request_class: 请求类
            router_prefix: 路由前缀
            tag: 标签
            description: 描述
        """
        self.service_class = service_class
        self.request_class = request_class
        self.router = APIRouter()
        self.tag = tag
        self.description = description

        # 创建依赖注入函数
        self.get_service = create_service_dependency(service_class)

        # 注册路由
        self._register_routes()

    def _register_routes(self):
        """注册所有路由"""
        self.router.add_api_route(
            "/data",
            self.get_data,
            methods=["GET"],
            response_model=APIResponse,
            summary=f"获取{self.description}数据",
            description=f"获取{self.description}数据，支持字段选择、日期范围过滤等功能",
        )

        self.router.add_api_route(
            "/health",
            self.health_check,
            methods=["GET"],
            response_model=HealthResponse,
            summary=f"{self.description}服务健康检查",
            description=f"检查{self.description}服务的健康状态",
        )

        self.router.add_api_route(
            "/fields",
            self.get_available_fields,
            methods=["GET"],
            response_model=FieldsResponse,
            summary=f"获取{self.description}可用字段",
            description=f"获取{self.description}的可用字段列表",
        )

        self.router.add_api_route(
            "/validate",
            self.validate_fields,
            methods=["POST"],
            response_model=ValidationResponse,
            summary=f"验证{self.description}字段",
            description=f"验证指定字段在{self.description}中是否存在",
        )

    async def get_data(
        self,
        ts_code: str = Query(..., description="股票代码（如：600519.SH）"),
        fields: str = Query(..., description="字段列表，逗号分隔"),
        start_date: Optional[str] = Query(None, description="开始日期，格式：YYYYMMDD"),
        end_date: Optional[str] = Query(None, description="结束日期，格式：YYYYMMDD"),
        service: T = Depends(self.get_service),
    ):
        """
        获取财务数据（通用方法）
        """
        # 验证公共参数
        field_list = validate_common_params(ts_code, fields, start_date, end_date)

        try:
            # 创建请求对象
            request = self.request_class(
                ts_code=ts_code,
                fields=field_list,
                start_date=start_date,
                end_date=end_date,
            )

            # 调用Service层获取数据
            response = await service.get_data(request)

            # 转换为API响应格式
            return create_api_response(response)

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"服务内部错误：{str(e)}")

    async def health_check(self, service: T = Depends(self.get_service)):
        """
        健康检查（通用方法）
        """
        try:
            health_status = await service.health_check()
            return create_health_response(health_status)

        except Exception as e:
            return HealthResponse(
                status="unhealthy",
                message=f"健康检查失败：{str(e)}",
                data_source="error",
                timestamp=datetime.now().timestamp(),
            )

    async def get_available_fields(
        self,
        ts_code: str = Query(..., description="股票代码"),
        start_date: Optional[str] = Query(None, description="开始日期，格式：YYYYMMDD"),
        end_date: Optional[str] = Query(None, description="结束日期，格式：YYYYMMDD"),
        service: T = Depends(self.get_service),
    ):
        """
        获取可用字段列表（通用方法）
        """
        if not ts_code:
            raise HTTPException(status_code=422, detail="股票代码不能为空")

        try:
            fields = await service.get_available_fields(ts_code, start_date, end_date)
            return create_fields_response(fields)

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"获取字段列表失败：{str(e)}")

    async def validate_fields(
        self,
        ts_code: str = Query(..., description="股票代码"),
        fields: List[str] = Query(..., description="要验证的字段列表"),
        start_date: Optional[str] = Query(None, description="开始日期，格式：YYYYMMDD"),
        end_date: Optional[str] = Query(None, description="结束日期，格式：YYYYMMDD"),
        service: T = Depends(self.get_service),
    ):
        """
        验证字段是否存在（通用方法）
        """
        if not ts_code:
            raise HTTPException(status_code=422, detail="股票代码不能为空")

        if not fields:
            raise HTTPException(status_code=422, detail="字段列表不能为空")

        try:
            validation_result = await service.validate_fields(
                ts_code, fields, start_date, end_date
            )
            return create_validation_response(validation_result)

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"字段验证失败：{str(e)}")

    def get_router(self) -> APIRouter:
        """获取路由器"""
        return self.router


# 导出基类
__all__ = ["BaseFinancialRoutes"]
