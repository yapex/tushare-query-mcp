"""
股票信息服务

提供股票基本信息的查询服务。
"""

import logging
from typing import Any, Dict, List, Optional

from ..schemas.request import StockDataSourceRequest, StockRequest
from ..schemas.response import (ResponseStatus, StockResponse,
                                create_stock_response)
from .base_service import BaseFinancialService
from .tushare_datasource import TushareDataSource

# 配置日志
logger = logging.getLogger(__name__)


class StockService(BaseFinancialService):
    """股票信息服务"""

    def __init__(self, tushare_token: str):
        """
        初始化股票信息服务

        Args:
            tushare_token: Tushare API token
        """
        super().__init__(tushare_token, "股票信息")

    async def get_stock_data(self, request: StockRequest) -> StockResponse:
        """
        获取股票数据

        Args:
            request: 股票请求

        Returns:
            股票响应
        """
        return await self.get_data(request)

    async def _get_data_from_source(
        self, request: StockDataSourceRequest
    ) -> List[Dict[str, Any]]:
        """
        从数据源获取股票数据

        Args:
            request: 数据源请求

        Returns:
            原始数据列表
        """
        # 这里暂时返回示例数据，实际应该调用TushareDataSource
        return await self.tushare_source.get_stock_data(request)

    def _create_response(
        self, data: List[Dict[str, Any]], message: str = "", **kwargs
    ) -> StockResponse:
        """
        创建股票响应

        Args:
            data: 数据
            message: 消息
            **kwargs: 其他参数

        Returns:
            股票响应
        """
        return create_stock_response(
            data=data, message=message or "股票信息查询成功", **kwargs
        )

    def _get_error_code(self) -> str:
        """
        获取股票错误代码

        Returns:
            错误代码
        """
        return "STOCK_QUERY_ERROR"

    def _create_data_source_request(
        self, request: StockRequest
    ) -> StockDataSourceRequest:
        """
        创建股票数据源请求

        Args:
            request: 服务层请求

        Returns:
            数据源请求
        """
        return StockDataSourceRequest(
            ts_code=request.ts_code,
            start_date=request.start_date,
            end_date=request.end_date,
        )

    def _create_data_source_request_by_dates(
        self, ts_code: str, start_date: Optional[str], end_date: Optional[str]
    ) -> StockDataSourceRequest:
        """
        根据日期创建股票数据源请求

        Args:
            ts_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            数据源请求
        """
        return StockDataSourceRequest(
            ts_code=ts_code, start_date=start_date, end_date=end_date
        )


# 便捷函数
async def create_stock_service(tushare_token: str) -> StockService:
    """
    创建StockService实例的便捷函数

    Args:
        tushare_token: Tushare API token

    Returns:
        StockService实例
    """
    return StockService(tushare_token)


# 导出主要接口
__all__ = [
    "StockService",
    "create_stock_service",
]
