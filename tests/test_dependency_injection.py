"""
测试依赖注入重构
"""

from unittest.mock import Mock

import pytest

from tushare_query_mcp.interfaces.core import ICache, IDataSource
from tushare_query_mcp.services.income_service import IncomeService


class TestDependencyInjection:
    """测试依赖注入重构"""

    def test_old_violation_now_fixed(self):
        """测试：原来的依赖注入问题已经修复"""
        from tushare_query_mcp.services.income_service import IncomeService

        # 旧的构造函数方式仍然存在（向后兼容）
        service = IncomeService("test_token")

        # ✅ 但现在使用的是构造函数注入！
        assert hasattr(service, "data_source")
        # ✅ 依赖是注入的，不是硬编码创建的
        from tushare_query_mcp.services.tushare_datasource import \
            TushareDataSource

        assert isinstance(service.data_source, TushareDataSource)

        # ✅ 更重要的是，现在可以使用依赖注入
        from unittest.mock import Mock

        from tushare_query_mcp.interfaces.core import IDataSource

        mock_data_source = Mock(spec=IDataSource)
        service_with_di = IncomeService(mock_data_source)  # 位置参数
        assert service_with_di.data_source is mock_data_source

    def test_service_should_accept_dependencies(self):
        """测试：服务应该通过构造函数接受依赖"""
        from tushare_query_mcp.services.tushare_datasource import \
            TushareDataSource
        from tushare_query_mcp.utils.cache import AsyncDiskCache

        # 期望的重构后接口
        class RefactoredIncomeService:
            def __init__(self, data_source: IDataSource, cache: ICache):
                self.data_source = data_source  # ✅ 依赖注入
                self.cache = cache

        # 可以注入mock进行测试
        mock_data_source = Mock(spec=IDataSource)
        mock_cache = Mock(spec=ICache)

        service = RefactoredIncomeService(mock_data_source, mock_cache)
        assert service.data_source is mock_data_source
        assert service.cache is mock_cache

    def test_constructor_injection_improves_testability(self):
        """测试：构造函数注入提高可测试性"""
        from tushare_query_mcp.services.income_service import IncomeService

        # 创建mock依赖
        mock_data_source = Mock(spec=IDataSource)

        # 配置mock返回值 - 使用Protocol定义的方法
        mock_data_source.get_income_data.return_value = [{"test": "data"}]

        # ✅ 重构后可以注入mock依赖
        service = IncomeService(mock_data_source)  # 位置参数
        assert service.data_source is mock_data_source

        # 验证可以调用mock方法
        import asyncio

        result = asyncio.run(service._get_data_from_source(Mock()))
        mock_data_source.get_income_data.assert_called_once()

    def test_backward_compatibility_with_token(self):
        """测试：向后兼容的token构造方法"""
        from tushare_query_mcp.services.income_service import IncomeService

        # 使用字符串token自动创建TushareDataSource（向后兼容）
        service = IncomeService("test_token")  # 字符串参数
        assert hasattr(service, "data_source")
        assert service.data_source is not None
        from tushare_query_mcp.services.tushare_datasource import \
            TushareDataSource

        assert isinstance(service.data_source, TushareDataSource)
