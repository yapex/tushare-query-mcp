"""
异步缓存管理器

基于 diskcache 实现的持久化缓存系统，支持 TTL、异步操作和智能键生成。
缓存重启后依然有效，大幅提升查询性能。
"""

import asyncio
import hashlib
import json
import logging
import os
import time
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from diskcache import Cache

# 配置日志
logger = logging.getLogger(__name__)


def memoize(cache_instance=None, expire=86400):
    """
    简单的 memoize 装饰器实现

    Args:
        cache_instance: 缓存实例
        expire: 过期时间（秒）

    Returns:
        装饰器函数
    """
    if cache_instance is None:
        cache_instance = Cache("./.cache")

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            key_data = {
                "func": func.__name__,
                "args": args,
                "kwargs": sorted(kwargs.items()),
            }
            key = hashlib.md5(
                json.dumps(key_data, sort_keys=True, default=str).encode()
            ).hexdigest()

            # 尝试从缓存获取
            result = cache_instance.get(key)
            if result is not None:
                # 检查是否过期
                if isinstance(result, dict) and "timestamp" in result:
                    elapsed = time.time() - result["timestamp"]
                    if elapsed < expire:
                        return result["data"]
                else:
                    cache_instance.delete(key)

            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache_data = {"data": result, "timestamp": time.time(), "ttl": expire}
            cache_instance.set(key, cache_data, expire=expire)
            return result

        return wrapper

    return decorator


class AsyncDiskCache:
    """异步磁盘缓存管理器"""

    def __init__(self, cache_dir: str = "./.cache"):
        """
        初始化缓存管理器

        Args:
            cache_dir: 缓存目录路径
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # 创建 diskcache 实例
        self.cache = Cache(str(self.cache_dir))

        logger.info(f"缓存管理器初始化完成，缓存目录: {self.cache_dir}")

    async def get(self, key: str) -> Optional[Any]:
        """
        获取缓存数据

        Args:
            key: 缓存键

        Returns:
            缓存的数据，如果不存在或已过期则返回 None
        """
        try:
            cache_data = self.cache.get(key)
            if cache_data is None:
                return None

            # 检查是否过期
            if self._is_expired(cache_data):
                logger.debug(f"缓存已过期: {key}")
                await self.delete(key)
                return None

            logger.debug(f"缓存命中: {key}")
            return cache_data["data"]

        except Exception as e:
            logger.error(f"获取缓存失败 {key}: {e}")
            return None

    async def set(self, key: str, data: Any, ttl: int = 3600) -> bool:
        """
        设置缓存数据

        Args:
            key: 缓存键
            data: 要缓存的数据
            ttl: 生存时间（秒）

        Returns:
            是否设置成功
        """
        try:
            cache_data = {"data": data, "timestamp": time.time(), "ttl": ttl}

            # 使用 expire 参数设置过期时间
            self.cache.set(key, cache_data, expire=ttl)
            logger.debug(f"缓存设置成功: {key}, TTL: {ttl}秒")
            return True

        except Exception as e:
            logger.error(f"设置缓存失败 {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        删除缓存数据

        Args:
            key: 缓存键

        Returns:
            是否删除成功
        """
        try:
            result = self.cache.delete(key)
            if result:
                logger.debug(f"缓存删除成功: {key}")
            else:
                logger.debug(f"缓存键不存在: {key}")
            return result

        except Exception as e:
            logger.error(f"删除缓存失败 {key}: {e}")
            return False

    async def clear(self) -> bool:
        """
        清空所有缓存

        Returns:
            是否清空成功
        """
        try:
            self.cache.clear()
            logger.info("所有缓存已清空")
            return True

        except Exception as e:
            logger.error(f"清空缓存失败: {e}")
            return False

    def stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            缓存统计信息
        """
        try:
            size = len(self.cache)
            volume = self.cache.volume()

            return {
                "size": size,
                "memory_usage": f"{volume / 1024 / 1024:.2f} MB",
                "cache_dir": str(self.cache_dir),
            }

        except Exception as e:
            logger.error(f"获取缓存统计失败: {e}")
            return {"size": 0, "memory_usage": "0 MB", "cache_dir": str(self.cache_dir)}

    def _is_expired(self, cache_data: Dict[str, Any]) -> bool:
        """
        检查缓存是否过期

        Args:
            cache_data: 缓存数据

        Returns:
            是否已过期
        """
        if "timestamp" not in cache_data or "ttl" not in cache_data:
            return True

        elapsed = time.time() - cache_data["timestamp"]
        return elapsed > cache_data["ttl"]

    def _generate_cache_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """
        生成缓存键

        Args:
            func_name: 函数名
            args: 位置参数
            kwargs: 关键字参数

        Returns:
            缓存键
        """
        # 创建可序列化的键数据
        key_data = {"func": func_name, "args": args, "kwargs": sorted(kwargs.items())}

        # 转换为 JSON 字符串并生成哈希
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()

    def cached_async(self, expire: int = 3600, key_prefix: str = ""):
        """
        异步函数缓存装饰器

        Args:
            expire: 缓存过期时间（秒）
            key_prefix: 键前缀

        Returns:
            装饰器函数
        """

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                # 生成缓存键
                cache_key = self._generate_cache_key(func.__name__, args, kwargs)
                if key_prefix:
                    cache_key = f"{key_prefix}:{cache_key}"

                # 尝试从缓存获取
                cached_result = await self.get(cache_key)
                if cached_result is not None:
                    return cached_result

                # 缓存未命中，执行原函数
                result = await func(*args, **kwargs)

                # 存入缓存
                await self.set(cache_key, result, ttl=expire)
                return result

            return async_wrapper

        return decorator

    def memoize_with_ttl(self, expire: int = 3600):
        """
        带TTL的memoize装饰器

        Args:
            expire: 缓存过期时间（秒）

        Returns:
            装饰器函数
        """
        return memoize(self.cache, expire=expire)

    async def exists(self, key: str) -> bool:
        """
        检查缓存是否存在

        Args:
            key: 缓存键

        Returns:
            bool: 缓存是否存在
        """
        try:
            cache_data = self.cache.get(key)
            if cache_data is None:
                return False

            # 检查是否过期
            if self._is_expired(cache_data):
                self.delete(key)
                return False

            return True

        except Exception as e:
            logger.error(f"检查缓存存在性失败 {key}: {e}")
            return False

    async def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            Dict[str, Any]: 缓存统计信息
        """
        try:
            return {
                "cache_dir": str(self.cache_dir),
                "cache_size": len(self.cache),
                "volume": self.cache.volume(),
                "size_limit": self.cache.size_limit,
                "eviction_policy": getattr(self.cache, "eviction_policy", "unknown"),
            }
        except Exception as e:
            logger.error(f"获取缓存统计信息失败: {e}")
            return {
                "cache_dir": str(self.cache_dir),
                "cache_size": 0,
                "volume": 0,
                "size_limit": 0,
                "eviction_policy": "unknown",
                "error": str(e),
            }

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        # 可以在这里执行清理操作
        pass


class CacheManager:
    """全局缓存管理器单例"""

    _instance: Optional[AsyncDiskCache] = None

    @classmethod
    def get_instance(cls, cache_dir: str = "./.cache") -> AsyncDiskCache:
        """
        获取全局缓存管理器实例

        Args:
            cache_dir: 缓存目录

        Returns:
            缓存管理器实例
        """
        if cls._instance is None:
            cls._instance = AsyncDiskCache(cache_dir)
        return cls._instance

    @classmethod
    def memoize_with_ttl(cls, expire: int = 3600, cache_dir: str = "./.cache"):
        """
        全局memoize装饰器

        Args:
            expire: 缓存过期时间（秒）
            cache_dir: 缓存目录

        Returns:
            装饰器函数
        """
        cache_manager = cls.get_instance(cache_dir)
        return memoize(cache_manager.cache, expire=expire)


# 全局缓存管理器实例
cache_manager = CacheManager.get_instance()


# 缓存配置常量
DEFAULT_CACHE_TTL = 86400  # 24小时
INCOME_CACHE_TTL = 86400 * 7  # 利润表缓存7天
BALANCE_CACHE_TTL = 86400 * 7  # 资产负债表缓存7天
CASHFLOW_CACHE_TTL = 86400 * 7  # 现金流量表缓存7天
STOCK_CACHE_TTL = 86400 * 30  # 股票信息缓存30天

# 缓存键前缀
CACHE_PREFIX_INCOME = "income"
CACHE_PREFIX_BALANCE = "balance"
CACHE_PREFIX_CASHFLOW = "cashflow"
CACHE_PREFIX_STOCK = "stock"


def create_cache_key(prefix: str, ts_code: str, **params) -> str:
    """
    创建标准化的缓存键

    Args:
        prefix: 缓存前缀
        ts_code: 股票代码
        **params: 其他参数

    Returns:
        缓存键
    """
    key_data = {
        "prefix": prefix,
        "ts_code": ts_code,
        **{k: v for k, v in sorted(params.items()) if v is not None},
    }

    key_str = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(key_str.encode()).hexdigest()


def get_cache_ttl(data_type: str) -> int:
    """
    根据数据类型获取缓存TTL

    Args:
        data_type: 数据类型

    Returns:
        缓存时间（秒）
    """
    ttl_mapping = {
        "income": INCOME_CACHE_TTL,
        "balance": BALANCE_CACHE_TTL,
        "cashflow": CASHFLOW_CACHE_TTL,
        "stock": STOCK_CACHE_TTL,
    }

    return ttl_mapping.get(data_type, DEFAULT_CACHE_TTL)


# 导出主要接口
__all__ = [
    "AsyncDiskCache",
    "CacheManager",
    "cache_manager",
    "create_cache_key",
    "get_cache_ttl",
    # 缓存配置常量
    "DEFAULT_CACHE_TTL",
    "INCOME_CACHE_TTL",
    "BALANCE_CACHE_TTL",
    "CASHFLOW_CACHE_TTL",
    "STOCK_CACHE_TTL",
    "CACHE_PREFIX_INCOME",
    "CACHE_PREFIX_BALANCE",
    "CACHE_PREFIX_CASHFLOW",
    "CACHE_PREFIX_STOCK",
]
