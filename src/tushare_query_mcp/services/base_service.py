"""
财务数据服务基础类

提供财务数据服务的公共功能，包括数据过滤、字段选择等。
DataSource层已处理缓存，Service层专注于业务逻辑。
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ..schemas.request import DataSourceRequest, FinancialDataRequest
from ..schemas.response import (FinancialDataResponse, ResponseStatus,
                                create_error_response)
from ..utils.data_filter import filter_by_update_flag
from ..utils.field_selector import FieldSelector
from .tushare_datasource import TushareDataSource

# 配置日志
logger = logging.getLogger(__name__)


class BaseFinancialService(ABC):
    """财务数据服务基础类"""

    def __init__(self, tushare_token: str, service_name: str):
        """
        初始化财务数据服务

        Args:
            tushare_token: Tushare API token
            service_name: 服务名称
        """
        self.tushare_source = TushareDataSource(tushare_token)
        self.service_name = service_name

    @abstractmethod
    async def _get_data_from_source(
        self, request: DataSourceRequest
    ) -> List[Dict[str, Any]]:
        """
        从数据源获取数据的抽象方法，子类必须实现

        Args:
            request: 数据源请求

        Returns:
            原始数据列表
        """
        pass

    @abstractmethod
    def _create_response(
        self, data: List[Dict[str, Any]], message: str = "", **kwargs
    ) -> FinancialDataResponse:
        """
        创建响应的抽象方法，子类必须实现

        Args:
            data: 数据
            message: 消息
            **kwargs: 其他参数

        Returns:
            响应对象
        """
        pass

    @abstractmethod
    def _get_error_code(self) -> str:
        """
        获取错误代码的抽象方法，子类必须实现

        Returns:
            错误代码
        """
        pass

    async def get_data(self, request: FinancialDataRequest) -> FinancialDataResponse:
        """
        获取财务数据的通用方法
        DataSource层已处理缓存，这里专注于业务逻辑处理

        Args:
            request: 财务数据请求

        Returns:
            财务数据响应
        """
        start_time = time.time()

        try:
            logger.info(f"获取{self.service_name}数据: {request.ts_code}")

            # 转换为数据源请求
            data_source_request = self._create_data_source_request(request)

            # 从数据源获取数据（DataSource层会处理缓存）
            raw_data = await self._get_data_from_source(data_source_request)

            # 检查数据是否为空（支持DataFrame和列表）
            if hasattr(raw_data, "empty") and raw_data.empty:
                # pandas DataFrame
                is_empty = True
            elif hasattr(raw_data, "__len__") and len(raw_data) == 0:
                # 列表或其他序列
                is_empty = True
            else:
                is_empty = False

            if is_empty:
                query_time = time.time() - start_time
                return self._create_response(
                    data=[],
                    message=f"{self.service_name}查询成功，但无数据",
                    query_time=query_time,
                )

            # 应用数据过滤器（update_flag过滤）
            filtered_data = filter_by_update_flag(raw_data)

            # 选择指定字段
            selected_data = FieldSelector.select_fields(filtered_data, request.fields)

            query_time = time.time() - start_time
            logger.info(
                f"{self.service_name}数据处理完成: {len(selected_data)} 条记录，耗时 {query_time:.3f}秒"
            )

            return self._create_response(
                data=selected_data,
                message=f"{self.service_name}查询成功",
                from_cache=False,  # DataSource层已处理缓存
                query_time=query_time,
            )

        except Exception as e:
            query_time = time.time() - start_time
            logger.error(f"获取{self.service_name}数据失败 {request.ts_code}: {e}")

            return create_error_response(
                message=f"获取{self.service_name}数据失败: {str(e)}",
                error_code=self._get_error_code(),
                query_time=query_time,
            )

    @abstractmethod
    def _create_data_source_request(
        self, request: FinancialDataRequest
    ) -> DataSourceRequest:
        """
        创建数据源请求的抽象方法，子类必须实现

        Args:
            request: 服务层请求

        Returns:
            数据源请求
        """
        pass

    async def get_available_fields(
        self,
        ts_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[str]:
        """
        获取可用字段列表

        Args:
            ts_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            可用字段列表
        """
        try:
            # 创建获取所有字段的请求
            data_source_request = self._create_data_source_request_by_dates(
                ts_code, start_date, end_date
            )

            # 获取一条记录来查看字段
            raw_data = await self._get_data_from_source(data_source_request)

            # 检查数据是否为空（支持DataFrame和列表）
            if hasattr(raw_data, "empty") and not raw_data.empty:
                # pandas DataFrame
                has_data = True
            elif hasattr(raw_data, "__len__") and len(raw_data) > 0:
                # 列表或其他序列
                has_data = True
            else:
                has_data = False

            if has_data:
                available_fields = FieldSelector.get_available_fields(raw_data)
                logger.info(
                    f"获取{self.service_name}可用字段: {len(available_fields)} 个字段"
                )
                return available_fields
            else:
                logger.warning(f"未找到{self.service_name}数据: {ts_code}")
                return []

        except Exception as e:
            logger.error(f"获取{self.service_name}可用字段失败 {ts_code}: {e}")
            return []

    @abstractmethod
    def _create_data_source_request_by_dates(
        self, ts_code: str, start_date: Optional[str], end_date: Optional[str]
    ) -> DataSourceRequest:
        """
        根据日期创建数据源请求的抽象方法，子类必须实现

        Args:
            ts_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            数据源请求
        """
        pass

    async def validate_fields(
        self,
        ts_code: str,
        fields: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        验证字段是否存在

        Args:
            ts_code: 股票代码
            fields: 要验证的字段列表
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            验证结果
        """
        try:
            # 获取可用字段
            available_fields = await self.get_available_fields(
                ts_code, start_date, end_date
            )

            # 验证字段
            missing_fields = FieldSelector.validate_fields(
                [], fields
            )  # 使用空数据，只验证字段名
            invalid_fields = [
                field for field in fields if field not in available_fields
            ]

            result = {
                "valid": len(invalid_fields) == 0,
                "available_fields_count": len(available_fields),
                "requested_fields_count": len(fields),
                "missing_fields": invalid_fields,
                "available_fields": available_fields[:10],  # 只返回前10个字段作为示例
            }

            if not result["valid"]:
                logger.warning(f"字段验证失败: {len(invalid_fields)} 个无效字段")

            return result

        except Exception as e:
            logger.error(f"验证字段失败 {ts_code}: {e}")
            return {
                "valid": False,
                "error": str(e),
                "available_fields_count": 0,
                "requested_fields_count": len(fields),
                "missing_fields": fields,
                "available_fields": [],
            }

    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查

        Returns:
            健康检查结果
        """
        try:
            # 检查Tushare数据源（DataSource层会检查自己的缓存）
            data_source_health = await self.tushare_source.health_check()

            health_status = {
                "status": (
                    "healthy"
                    if data_source_health.get("status") == "healthy"
                    else "unhealthy"
                ),
                "message": (
                    "服务运行正常"
                    if data_source_health.get("status") == "healthy"
                    else "数据源异常"
                ),
                "data_source": data_source_health.get("status", "unknown"),
                "timestamp": time.time(),
            }

            return health_status

        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return {
                "status": "unhealthy",
                "message": f"健康检查失败: {str(e)}",
                "data_source": "error",
                "timestamp": time.time(),
            }

    def _calculate_yoy_change(self, previous: float, current: float) -> Dict[str, Any]:
        """
        计算同比变化的通用方法

        Args:
            previous: 上期值
            current: 本期值

        Returns:
            同比变化信息
        """
        if previous == 0:
            return {
                "absolute_change": current,
                "percentage_change": "infinite" if current != 0 else 0,
                "trend": (
                    "improving"
                    if current > 0
                    else "stable" if current == 0 else "declining"
                ),
            }

        absolute_change = current - previous
        percentage_change = (absolute_change / abs(previous)) * 100

        return {
            "absolute_change": absolute_change,
            "percentage_change": round(percentage_change, 2),
            "trend": (
                "improving"
                if absolute_change > 0
                else "stable" if absolute_change == 0 else "declining"
            ),
        }


# 导出主要接口
__all__ = [
    "BaseFinancialService",
]
