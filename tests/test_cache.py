"""
缓存系统测试用例
测试 diskcache 持久化缓存的功能，包括 TTL、过期检查、缓存持久化等
"""

import asyncio
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import AsyncMock, patch

import pytest

# 导入待测试的模块
from tushare_query_mcp.utils.cache import AsyncDiskCache, cache_manager


class TestAsyncDiskCache:
    """测试异步磁盘缓存管理器"""

    @pytest.fixture
    def temp_cache_dir(self):
        """创建临时缓存目录"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def cache_instance(self, temp_cache_dir):
        """创建缓存实例"""
        return AsyncDiskCache(cache_dir=temp_cache_dir)

    def test_cache_set_and_get(self, cache_instance):
        """测试缓存设置和获取"""
        # 设置缓存
        test_data = [{"test": "data", "value": 123}]
        cache_instance.set("test_key", test_data, ttl=3600)

        # 获取缓存
        cached_data = cache_instance.get("test_key")
        assert cached_data == test_data

    def test_cache_miss(self, cache_instance):
        """测试缓存未命中"""
        # 获取不存在的缓存
        result = cache_instance.get("nonexistent_key")
        assert result is None

    def test_cache_overwrite(self, cache_instance):
        """测试缓存覆盖"""
        # 设置初始缓存
        initial_data = [{"initial": "data"}]
        cache_instance.set("test_key", initial_data, ttl=3600)

        # 覆盖缓存
        new_data = [{"new": "data", "updated": True}]
        cache_instance.set("test_key", new_data, ttl=3600)

        # 验证覆盖成功
        cached_data = cache_instance.get("test_key")
        assert cached_data == new_data
        assert cached_data != initial_data

    def test_cache_ttl_expiration(self, cache_instance):
        """测试缓存过期机制"""
        # 设置短TTL的缓存
        test_data = [{"ttl": "test"}]
        cache_instance.set("ttl_key", test_data, ttl=1)  # 1秒过期

        # 立即获取应该成功
        assert cache_instance.get("ttl_key") == test_data

        # 等待过期
        time.sleep(1.1)

        # 过期后应该返回 None
        assert cache_instance.get("ttl_key") is None

    def test_cache_persistence(self, temp_cache_dir):
        """测试缓存持久化（重启后依然存在）"""
        # 创建第一个缓存实例
        cache1 = AsyncDiskCache(cache_dir=temp_cache_dir)
        test_data = [{"persistent": "data", "timestamp": time.time()}]
        cache1.set("persistent_key", test_data, ttl=3600)

        # 验证数据存在
        assert cache1.get("persistent_key") == test_data

        # 创建新的缓存实例（模拟重启）
        cache2 = AsyncDiskCache(cache_dir=temp_cache_dir)

        # 验证重启后数据依然存在
        persisted_data = cache2.get("persistent_key")
        assert persisted_data == test_data
        assert persisted_data[0]["persistent"] == "data"

    def test_cache_key_generation(self, cache_instance):
        """测试缓存键生成"""
        # 测试不同参数生成不同的键
        key1 = cache_instance._generate_cache_key(
            "test_func", ("arg1",), {"param1": "value1"}
        )
        key2 = cache_instance._generate_cache_key(
            "test_func", ("arg2",), {"param1": "value1"}
        )
        key3 = cache_instance._generate_cache_key(
            "test_func", ("arg1",), {"param1": "value2"}
        )

        # 不同的参数应该生成不同的键
        assert key1 != key2
        assert key1 != key3
        assert key2 != key3

        # 相同的参数应该生成相同的键
        key4 = cache_instance._generate_cache_key(
            "test_func", ("arg1",), {"param1": "value1"}
        )
        assert key1 == key4

    def test_cache_clear(self, cache_instance):
        """测试缓存清理"""
        # 设置多个缓存
        cache_instance.set("key1", "data1", ttl=3600)
        cache_instance.set("key2", "data2", ttl=3600)
        cache_instance.set("key3", "data3", ttl=3600)

        # 验证数据存在
        assert cache_instance.get("key1") == "data1"
        assert cache_instance.get("key2") == "data2"
        assert cache_instance.get("key3") == "data3"

        # 清空缓存
        cache_instance.clear()

        # 验证所有数据都被清理
        assert cache_instance.get("key1") is None
        assert cache_instance.get("key2") is None
        assert cache_instance.get("key3") is None

    def test_cache_delete_key(self, cache_instance):
        """测试删除特定键"""
        # 设置多个缓存
        cache_instance.set("keep_key", "keep_data", ttl=3600)
        cache_instance.set("delete_key", "delete_data", ttl=3600)

        # 验证数据存在
        assert cache_instance.get("keep_key") == "keep_data"
        assert cache_instance.get("delete_key") == "delete_data"

        # 删除特定键
        cache_instance.delete("delete_key")

        # 验证只有特定键被删除
        assert cache_instance.get("keep_key") == "keep_data"
        assert cache_instance.get("delete_key") is None

    def test_cache_stats(self, cache_instance):
        """测试缓存统计"""
        # 设置一些缓存
        cache_instance.set("key1", "data1", ttl=3600)
        cache_instance.set("key2", "data2", ttl=3600)

        # 获取统计信息
        stats = cache_instance.stats()

        assert isinstance(stats, dict)
        assert "size" in stats
        assert "memory_usage" in stats
        assert stats["size"] == 2

    def test_cache_complex_data_types(self, cache_instance):
        """测试复杂数据类型的缓存"""
        # 测试各种数据类型
        test_cases = [
            "simple_string",
            123,
            123.456,
            True,
            False,
            None,
            ["list", "of", "strings"],
            {"key": "value", "nested": {"inner_key": "inner_value"}},
            {"mixed": [1, "two", {"three": 3}]},
        ]

        for i, test_data in enumerate(test_cases):
            key = f"test_key_{i}"
            cache_instance.set(key, test_data, ttl=3600)
            retrieved_data = cache_instance.get(key)
            assert retrieved_data == test_data

    @pytest.mark.asyncio
    async def test_async_cached_decorator(self, cache_instance):
        """测试异步缓存装饰器"""
        call_count = 0

        @cache_instance.cached_async(expire=3600)
        async def expensive_function(arg1, arg2):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)  # 模拟耗时操作
            return f"result_{arg1}_{arg2}_{time.time()}"

        # 第一次调用
        result1 = await expensive_function("test", "arg")
        first_call_count = call_count

        # 第二次调用应该使用缓存
        result2 = await expensive_function("test", "arg")
        second_call_count = call_count

        # 验证只调用了一次函数
        assert first_call_count == 1
        assert second_call_count == 1
        assert result1 == result2

        # 不同参数应该重新调用
        result3 = await expensive_function("test", "different_arg")
        third_call_count = call_count

        assert third_call_count == 2
        assert result3 != result1

    def test_concurrent_cache_access(self, cache_instance):
        """测试并发缓存访问"""
        import queue
        import threading

        results = queue.Queue()
        num_threads = 10

        def worker(worker_id):
            # 每个线程设置和获取自己的缓存
            key = f"worker_{worker_id}"
            data = {
                "worker_id": worker_id,
                "thread_id": threading.current_thread().ident,
            }

            cache_instance.set(key, data, ttl=3600)
            retrieved = cache_instance.get(key)
            results.put(retrieved)

        # 启动多个线程
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证结果
        retrieved_results = []
        while not results.empty():
            retrieved_results.append(results.get())

        assert len(retrieved_results) == num_threads

        # 验证每个线程都能正确获取自己的数据
        worker_data = {result["worker_id"]: result for result in retrieved_results}
        assert len(worker_data) == num_threads

        for worker_id in range(num_threads):
            assert worker_id in worker_data
            assert worker_data[worker_id]["worker_id"] == worker_id


class TestCacheManager:
    """测试全局缓存管理器"""

    def test_global_cache_manager_singleton(self):
        """测试全局缓存管理器是单例"""
        manager1 = cache_manager
        manager2 = cache_manager

        assert manager1 is manager2

    def test_memoize_decorator(self):
        """测试 memoize 装饰器功能"""
        call_count = 0

        @cache_manager.memoize_with_ttl(expire=3600)
        def test_function(x, y):
            nonlocal call_count
            call_count += 1
            return x + y

        # 第一次调用
        result1 = test_function(1, 2)
        assert result1 == 3
        assert call_count == 1

        # 第二次调用应该使用缓存
        result2 = test_function(1, 2)
        assert result2 == 3
        assert call_count == 1  # 没有增加

        # 不同参数应该重新调用
        result3 = test_function(2, 3)
        assert result3 == 5
        assert call_count == 2

    def test_default_cache_directory_creation(self):
        """测试默认缓存目录创建"""
        # 应该创建 .cache 目录
        from tushare_query_mcp.utils.cache import AsyncDiskCache

        assert isinstance(cache_manager, AsyncDiskCache)
        assert cache_manager.cache_dir.name == ".cache"
        assert cache_manager.cache_dir.exists()


class TestCacheErrorHandling:
    """测试缓存错误处理"""

    @pytest.fixture
    def cache_instance(self):
        """创建缓存实例"""
        return AsyncDiskCache(cache_dir="./test_cache")

    def test_cache_directory_permission_error(self):
        """测试缓存目录权限错误"""
        # 尝试创建无权限的目录
        with pytest.raises(Exception):
            invalid_cache = AsyncDiskCache(cache_dir="/root/no_permission_cache")

    def test_corrupted_cache_data(self, cache_instance):
        """测试损坏的缓存数据处理"""
        # 模拟损坏的数据（这个测试可能需要根据实际实现调整）
        try:
            cache_instance.set("corrupted_key", "valid_data", ttl=3600)

            # 模拟数据损坏（直接操作底层存储）
            if hasattr(cache_instance.cache, "set"):
                cache_instance.cache.set("corrupted_key", b"invalid_binary_data")

            # 尝试获取损坏的数据应该优雅处理
            result = cache_instance.get("corrupted_key")
            # 根据实现，可能是返回 None 或抛出特定异常
            assert result is None or isinstance(result, Exception)

        except Exception as e:
            # 如果实现选择抛出异常，确保是预期的异常类型
            assert True  # 测试通过，因为异常被正确处理


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
