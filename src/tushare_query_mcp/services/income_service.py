"""
利润表服务

整合数据源、缓存、数据过滤和字段选择，提供完整的利润表业务逻辑。
"""

import logging
from typing import Any, Dict, List, Optional

from ..schemas.request import IncomeDataSourceRequest, IncomeRequest
from ..schemas.response import (IncomeResponse, ResponseStatus,
                                create_income_response)
from ..interfaces.core import IDataSource
from ..utils.data_filter import filter_by_update_flag
from ..utils.field_selector import FieldSelector
from .base_service import BaseFinancialService
from .tushare_datasource import TushareDataSource

# 配置日志
logger = logging.getLogger(__name__)


class IncomeService(BaseFinancialService):
    """利润表服务"""

    def __init__(self, data_source_or_token):
        """
        初始化利润表服务 - 支持依赖注入和向后兼容

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

        super().__init__(data_source, "利润表")

    async def get_income_data(self, request: IncomeRequest) -> IncomeResponse:
        """
        获取利润表数据

        Args:
            request: 利润表请求

        Returns:
            利润表响应
        """
        return await self.get_data(request)

    async def _get_data_from_source(
        self, request: IncomeDataSourceRequest
    ) -> List[Dict[str, Any]]:
        """
        从数据源获取利润表数据

        Args:
            request: 数据源请求

        Returns:
            原始数据列表
        """
        return await self.data_source.get_income_data(request)

    def _create_response(
        self, data: List[Dict[str, Any]], message: str = "", **kwargs
    ) -> IncomeResponse:
        """
        创建利润表响应

        Args:
            data: 数据
            message: 消息
            **kwargs: 其他参数

        Returns:
            利润表响应
        """
        return create_income_response(
            data=data, message=message or "利润表查询成功", **kwargs
        )

    def _get_error_code(self) -> str:
        """
        获取利润表错误代码

        Returns:
            错误代码
        """
        return "INCOME_QUERY_ERROR"

    def _create_data_source_request(
        self, request: IncomeRequest
    ) -> IncomeDataSourceRequest:
        """
        创建利润表数据源请求

        Args:
            request: 服务层请求

        Returns:
            数据源请求
        """
        return IncomeDataSourceRequest(
            ts_code=request.ts_code,
            start_date=request.start_date,
            end_date=request.end_date,
        )

    def _create_data_source_request_by_dates(
        self, ts_code: str, start_date: Optional[str], end_date: Optional[str]
    ) -> IncomeDataSourceRequest:
        """
        根据日期创建利润表数据源请求

        Args:
            ts_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            数据源请求
        """
        return IncomeDataSourceRequest(
            ts_code=ts_code, start_date=start_date, end_date=end_date
        )

    def _create_data_source_request_by_dates(
        self, ts_code: str, start_date: Optional[str], end_date: Optional[str]
    ) -> IncomeDataSourceRequest:
        """
        根据日期创建利润表数据源请求

        Args:
            ts_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            数据源请求
        """
        return IncomeDataSourceRequest(
            ts_code=ts_code, start_date=start_date, end_date=end_date
        )


# 便捷函数
async def create_income_service(tushare_token: str) -> IncomeService:
    """
    创建IncomeService实例的便捷函数

    Args:
        tushare_token: Tushare API token

    Returns:
        IncomeService实例
    """
    return IncomeService(tushare_token)


# 导出主要接口
__all__ = [
    "IncomeService",
    "create_income_service",
]
