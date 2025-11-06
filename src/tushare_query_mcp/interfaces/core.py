"""
核心依赖接口 - 简化设计
"""
from typing import Protocol, List, Dict, Any, Optional
from ..schemas.request import FinancialDataRequest


class IDataSource(Protocol):
    """数据源接口 - 最简化设计"""
    async def get_income_data(self, request: FinancialDataRequest) -> List[Dict[str, Any]]: ...
    async def get_balance_data(self, request: FinancialDataRequest) -> List[Dict[str, Any]]: ...
    async def get_cashflow_data(self, request: FinancialDataRequest) -> List[Dict[str, Any]]: ...
    async def health_check(self) -> bool: ...


class ICache(Protocol):
    """缓存接口 - 最简化设计"""
    async def get(self, key: str) -> Optional[List[Dict[str, Any]]]: ...
    async def set(self, key: str, data: List[Dict[str, Any]], expire: int) -> bool: ...


class IFinancialService(Protocol):
    """财务服务接口 - 最简化设计"""
    async def get_data(self, request: FinancialDataRequest) -> Dict[str, Any]: ...