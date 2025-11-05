"""
资产负债表服务

整合数据源、缓存、数据过滤和字段选择，提供完整的资产负债表业务逻辑。
"""

import logging
from typing import Any, Dict, List, Optional

from ..schemas.request import BalanceDataSourceRequest, BalanceRequest
from ..schemas.response import (BalanceResponse, ResponseStatus,
                                create_balance_response)
from .base_service import BaseFinancialService

# 配置日志
logger = logging.getLogger(__name__)


class BalanceService(BaseFinancialService):
    """资产负债表服务"""

    def __init__(self, tushare_token: str):
        """
        初始化资产负债表服务

        Args:
            tushare_token: Tushare API token
        """
        super().__init__(tushare_token, "资产负债表")

    async def get_balance_data(self, request: BalanceRequest) -> BalanceResponse:
        """
        获取资产负债表数据

        Args:
            request: 资产负债表请求

        Returns:
            资产负债表响应
        """
        return await self.get_data(request)

    async def _get_data_from_source(
        self, request: BalanceDataSourceRequest
    ) -> List[Dict[str, Any]]:
        """
        从数据源获取资产负债表数据

        Args:
            request: 数据源请求

        Returns:
            原始数据列表
        """
        return await self.tushare_source.get_balance_data(request)

    def _create_response(
        self, data: List[Dict[str, Any]], message: str = "", **kwargs
    ) -> BalanceResponse:
        """
        创建资产负债表响应

        Args:
            data: 数据
            message: 消息
            **kwargs: 其他参数

        Returns:
            资产负债表响应
        """
        return create_balance_response(
            data=data, message=message or "资产负债表查询成功", **kwargs
        )

    def _get_error_code(self) -> str:
        """
        获取资产负债表错误代码

        Returns:
            错误代码
        """
        return "BALANCE_QUERY_ERROR"

    def _create_data_source_request(
        self, request: BalanceRequest
    ) -> BalanceDataSourceRequest:
        """
        创建资产负债表数据源请求

        Args:
            request: 服务层请求

        Returns:
            数据源请求
        """
        return BalanceDataSourceRequest(
            ts_code=request.ts_code,
            start_date=request.start_date,
            end_date=request.end_date,
        )

    def _create_data_source_request_by_dates(
        self, ts_code: str, start_date: Optional[str], end_date: Optional[str]
    ) -> BalanceDataSourceRequest:
        """
        根据日期创建资产负债表数据源请求

        Args:
            ts_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            数据源请求
        """
        return BalanceDataSourceRequest(
            ts_code=ts_code, start_date=start_date, end_date=end_date
        )


# 便捷函数
async def create_balance_service(tushare_token: str) -> BalanceService:
    """
    创建BalanceService实例的便捷函数

    Args:
        tushare_token: Tushare API token

    Returns:
        BalanceService实例
    """
    return BalanceService(tushare_token)


# 导出主要接口
__all__ = [
    "BalanceService",
    "create_balance_service",
]
