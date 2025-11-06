"""
现金流量表服务

整合数据源、缓存、数据过滤和字段选择，提供完整的现金流量表业务逻辑。
"""

import logging
from typing import Any, Dict, List, Optional

from ..schemas.request import CashFlowDataSourceRequest, CashFlowRequest
from ..schemas.response import (CashFlowResponse, ResponseStatus,
                                create_cashflow_response)
from ..interfaces.core import IDataSource
from .base_service import BaseFinancialService
from .tushare_datasource import TushareDataSource

# 配置日志
logger = logging.getLogger(__name__)


class CashFlowService(BaseFinancialService):
    """现金流量表服务"""

    def __init__(self, data_source_or_token):
        """
        初始化现金流量表服务 - 支持依赖注入和向后兼容

        Args:
            data_source_or_token: 数据源接口实现或token字符串（向后兼容）
        """
        # 检查是否是token字符串（向后兼容）
        if isinstance(data_source_or_token, str):
            # 向后兼容：自动创建TushareDataSource
            data_source = TushareDataSource(data_source_or_token)
        else:
            # 新方式：使用注入的数据源
            data_source = data_source_or_token

        super().__init__(data_source, "现金流量表")

    async def get_cashflow_data(self, request: CashFlowRequest) -> CashFlowResponse:
        """
        获取现金流量表数据

        Args:
            request: 现金流量表请求

        Returns:
            现金流量表响应
        """
        return await self.get_data(request)

    async def _get_data_from_source(
        self, request: CashFlowDataSourceRequest
    ) -> List[Dict[str, Any]]:
        """
        从数据源获取现金流量表数据

        Args:
            request: 数据源请求

        Returns:
            原始数据列表
        """
        return await self.data_source.get_cashflow_data(request)

    def _create_response(
        self, data: List[Dict[str, Any]], message: str = "", **kwargs
    ) -> CashFlowResponse:
        """
        创建现金流量表响应

        Args:
            data: 数据
            message: 消息
            **kwargs: 其他参数

        Returns:
            现金流量表响应
        """
        return create_cashflow_response(
            data=data, message=message or "现金流量表查询成功", **kwargs
        )

    def _get_error_code(self) -> str:
        """
        获取现金流量表错误代码

        Returns:
            错误代码
        """
        return "CASHFLOW_QUERY_ERROR"

    def _create_data_source_request(
        self, request: CashFlowRequest
    ) -> CashFlowDataSourceRequest:
        """
        创建现金流量表数据源请求

        Args:
            request: 服务层请求

        Returns:
            数据源请求
        """
        return CashFlowDataSourceRequest(
            ts_code=request.ts_code,
            start_date=request.start_date,
            end_date=request.end_date,
        )

    def _create_data_source_request_by_dates(
        self, ts_code: str, start_date: Optional[str], end_date: Optional[str]
    ) -> CashFlowDataSourceRequest:
        """
        根据日期创建现金流量表数据源请求

        Args:
            ts_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            数据源请求
        """
        return CashFlowDataSourceRequest(
            ts_code=ts_code, start_date=start_date, end_date=end_date
        )


# 便捷函数
async def create_cashflow_service(tushare_token: str) -> CashFlowService:
    """
    创建CashFlowService实例的便捷函数

    Args:
        tushare_token: Tushare API token

    Returns:
        CashFlowService实例
    """
    return CashFlowService(tushare_token)


# 导出主要接口
__all__ = [
    "CashFlowService",
    "create_cashflow_service",
]
