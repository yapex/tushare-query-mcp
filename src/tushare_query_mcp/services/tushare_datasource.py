"""
Tushare数据源

提供异步的Tushare API调用封装，负责获取完整的财务数据。
按照架构设计，该层不进行字段过滤，总是返回所有可用字段。
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

try:
    import tushare as ts
except ImportError:
    ts = None

from ..schemas.request import (BalanceDataSourceRequest,
                               CashFlowDataSourceRequest,
                               FinancialDataRequest,
                               IncomeDataSourceRequest, StockDataSourceRequest)

# 配置日志
logger = logging.getLogger(__name__)


class TushareDataSource:
    """Tushare数据源"""

    def __init__(self, token: str):
        """
        初始化Tushare数据源

        Args:
            token: Tushare API token

        Raises:
            ValueError: 当token为空时
            ImportError: 当tushare库未安装时
        """
        if ts is None:
            raise ImportError("tushare库未安装，请运行: uv add tushare")

        if not token or not token.strip():
            raise ValueError("Tushare token不能为空")

        self.token = token.strip()

        # 设置tushare token
        ts.set_token(self.token)

        # 初始化pro API
        self.pro = ts.pro_api()

        logger.info("Tushare数据源初始化完成")

    def _build_api_parameters(self, request) -> Dict[str, Any]:
        """
        构建API调用参数

        Args:
            request: 数据源请求对象

        Returns:
            API参数字典
        """
        params = {"ts_code": request.ts_code}

        # 添加可选的日期参数
        if hasattr(request, "start_date") and request.start_date:
            params["start_date"] = request.start_date

        if hasattr(request, "end_date") and request.end_date:
            params["end_date"] = request.end_date

        return params

    async def get_income_data(
        self, request: FinancialDataRequest
    ) -> List[Dict[str, Any]]:
        """
        获取利润表数据

        Args:
            request: 财务数据请求对象

        Returns:
            利润表数据列表（包含所有字段）
        """
        logger.info(f"获取利润表数据: {request.ts_code}")

        try:
            # 转换为内部请求类型
            internal_request = IncomeDataSourceRequest(
                ts_code=request.ts_code,
                start_date=request.start_date,
                end_date=request.end_date
            )
            params = self._build_api_parameters(internal_request)

            # 在异步上下文中调用同步API
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: self.pro.income(**params))

            # 将pandas DataFrame转换为字典列表
            if hasattr(data, "to_dict"):
                data = data.to_dict("records")
            elif isinstance(data, list):
                # 如果已经是列表，确保每个元素都是字典
                data = [
                    dict(record) if hasattr(record, "to_dict") else record
                    for record in data
                ]

            logger.info(f"成功获取利润表数据: {len(data)} 条记录")
            return data

        except Exception as e:
            logger.error(f"获取利润表数据失败 {request.ts_code}: {e}")
            raise

    async def get_balance_data(
        self, request: FinancialDataRequest
    ) -> List[Dict[str, Any]]:
        """
        获取资产负债表数据

        Args:
            request: 财务数据请求对象

        Returns:
            资产负债表数据列表（包含所有字段）
        """
        logger.info(f"获取资产负债表数据: {request.ts_code}")

        try:
            # 转换为内部请求类型
            internal_request = BalanceDataSourceRequest(
                ts_code=request.ts_code,
                start_date=request.start_date,
                end_date=request.end_date
            )
            params = self._build_api_parameters(internal_request)

            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(
                None, lambda: self.pro.balancesheet(**params)
            )

            # 将pandas DataFrame转换为字典列表
            if hasattr(data, "to_dict"):
                data = data.to_dict("records")
            elif isinstance(data, list):
                # 如果已经是列表，确保每个元素都是字典
                data = [
                    dict(record) if hasattr(record, "to_dict") else record
                    for record in data
                ]

            logger.info(f"成功获取资产负债表数据: {len(data)} 条记录")
            return data

        except Exception as e:
            logger.error(f"获取资产负债表数据失败 {request.ts_code}: {e}")
            raise

    async def get_cashflow_data(
        self, request: FinancialDataRequest
    ) -> List[Dict[str, Any]]:
        """
        获取现金流量表数据

        Args:
            request: 财务数据请求对象

        Returns:
            现金流量表数据列表（包含所有字段）
        """
        logger.info(f"获取现金流量表数据: {request.ts_code}")

        try:
            # 转换为内部请求类型
            internal_request = CashFlowDataSourceRequest(
                ts_code=request.ts_code,
                start_date=request.start_date,
                end_date=request.end_date
            )
            params = self._build_api_parameters(internal_request)

            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: self.pro.cashflow(**params))

            # 将pandas DataFrame转换为字典列表
            if hasattr(data, "to_dict"):
                data = data.to_dict("records")
            elif isinstance(data, list):
                # 如果已经是列表，确保每个元素都是字典
                data = [
                    dict(record) if hasattr(record, "to_dict") else record
                    for record in data
                ]

            logger.info(f"成功获取现金流量表数据: {len(data)} 条记录")
            return data

        except Exception as e:
            logger.error(f"获取现金流量表数据失败 {request.ts_code}: {e}")
            raise

    async def get_stock_data(
        self, request: StockDataSourceRequest
    ) -> List[Dict[str, Any]]:
        """
        获取股票基本信息数据

        Args:
            request: 股票信息数据源请求

        Returns:
            股票基本信息数据列表（包含所有字段）
        """
        logger.info(f"获取股票基本信息数据: {request.ts_code}")

        try:
            # 股票基本信息API使用stock_basic方法
            params = {"ts_code": request.ts_code}

            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(
                None, lambda: self.pro.stock_basic(**params)
            )

            logger.info(f"成功获取股票基本信息数据: {len(data)} 条记录")
            return data

        except Exception as e:
            logger.error(f"获取股票基本信息数据失败 {request.ts_code}: {e}")
            raise

    async def get_all_financial_data(
        self,
        ts_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        并发获取所有财务数据

        Args:
            ts_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            包含所有财务数据的字典
        """
        logger.info(f"并发获取所有财务数据: {ts_code}")

        # 创建请求对象
        income_request = IncomeDataSourceRequest(
            ts_code=ts_code, start_date=start_date, end_date=end_date
        )
        balance_request = BalanceDataSourceRequest(
            ts_code=ts_code, start_date=start_date, end_date=end_date
        )
        cashflow_request = CashFlowDataSourceRequest(
            ts_code=ts_code, start_date=start_date, end_date=end_date
        )

        try:
            # 并发执行所有请求
            income_data, balance_data, cashflow_data = await asyncio.gather(
                self.get_income_data(income_request),
                self.get_balance_data(balance_request),
                self.get_cashflow_data(cashflow_request),
                return_exceptions=True,
            )

            # 检查是否有异常
            results = {}

            if isinstance(income_data, Exception):
                logger.error(f"利润表数据获取失败: {income_data}")
                results["income"] = []
            else:
                results["income"] = income_data

            if isinstance(balance_data, Exception):
                logger.error(f"资产负债表数据获取失败: {balance_data}")
                results["balance"] = []
            else:
                results["balance"] = balance_data

            if isinstance(cashflow_data, Exception):
                logger.error(f"现金流量表数据获取失败: {cashflow_data}")
                results["cashflow"] = []
            else:
                results["cashflow"] = cashflow_data

            total_records = sum(len(data) for data in results.values())
            logger.info(f"成功获取财务数据总计: {total_records} 条记录")

            return results

        except Exception as e:
            logger.error(f"获取财务数据失败 {ts_code}: {e}")
            raise

    async def health_check(self) -> bool:
        """
        健康检查，测试API连接是否正常

        Returns:
            bool: 数据源是否健康
        """
        try:
            # 尝试调用一个简单的API来测试连接
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.pro.trade_cal(
                    exchange="SSE", start_date="20240101", end_date="20240101"
                ),
            )

            is_healthy = len(result) > 0 if hasattr(result, '__len__') else False
            if is_healthy:
                logger.info("健康检查通过：Tushare API连接正常")
            else:
                logger.warning("健康检查失败：API返回空结果")

            return is_healthy

        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return False

    async def detailed_health_check(self) -> Dict[str, Any]:
        """
        详细健康检查，返回详细信息（用于调试）

        Returns:
            健康检查详细结果
        """
        try:
            # 尝试调用一个简单的API来测试连接
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.pro.trade_cal(
                    exchange="SSE", start_date="20240101", end_date="20240101"
                ),
            )

            return {
                "status": "healthy",
                "message": "Tushare API连接正常",
                "token_length": len(self.token),
                "test_api_result": len(result) if hasattr(result, '__len__') else 0,
            }

        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return {
                "status": "unhealthy",
                "message": f"Tushare API连接失败: {str(e)}",
                "token_length": len(self.token) if self.token else 0,
                "test_api_result": 0,
            }


# 导出主要接口
__all__ = [
    "TushareDataSource",
]
