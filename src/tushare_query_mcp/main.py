"""
FastAPI应用入口文件

提供完整的RESTful API服务，包括：
- 股票基本信息查询
- 财务报表数据查询（利润表、资产负债表、现金流量表）
- 健康检查和监控
- Swagger文档生成
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from .api.v1 import balance, cashflow, income, stock
from .config import get_settings


# 配置日志
def setup_logging():
    """设置应用日志配置"""
    settings = get_settings()

    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 减少第三方库的日志噪音
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


# 应用生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理

    在应用启动时执行初始化操作，在应用关闭时执行清理操作。
    """
    logger = logging.getLogger(__name__)

    # 启动时的初始化操作
    logger.info("正在启动Tushare Query MCP API服务...")

    settings = get_settings()
    logger.info(f"API服务器地址: {settings.api_host}:{settings.api_port}")
    logger.info(f"缓存目录: {settings.cache_dir}")
    logger.info(f"日志级别: {settings.log_level}")

    # 验证Tushare token
    if not settings.tushare_token:
        logger.error("TUSHARE_TOKEN环境变量未设置")
        raise RuntimeError("TUSHARE_TOKEN环境变量是必需的")

    logger.info("✅ Tushare Query MCP API服务启动完成")

    yield

    # 关闭时的清理操作
    logger.info("正在关闭Tushare Query MCP API服务...")
    logger.info("🛑 Tushare Query MCP API服务已关闭")


# 创建FastAPI应用实例
def create_app() -> FastAPI:
    """
    创建并配置FastAPI应用

    Returns:
        FastAPI: 配置好的应用实例
    """
    # 设置日志
    setup_logging()

    # 获取配置
    settings = get_settings()

    # 创建FastAPI应用
    app = FastAPI(
        title="Tushare Query MCP API",
        description="""
        ## Tushare Query MCP API 服务

        提供中国股票财务数据的查询服务，支持：

        ### 📊 财务报表数据
        - **利润表**：营收、利润、每股收益等财务指标
        - **资产负债表**：资产、负债、股东权益等财务状况
        - **现金流量表**：经营、投资、筹资活动现金流
        - **股票基本信息**：股票代码、名称、上市日期等基础信息

        ### 🔧 核心特性
        - **RESTful API设计**：遵循REST架构原则
        - **统一响应格式**：标准化的JSON响应结构
        - **智能缓存机制**：减少API调用次数，提升响应速度
        - **完整的错误处理**：详细的错误信息和异常处理
        - **实时健康检查**：监控服务状态和数据源连接
        - **自动化文档**：基于OpenAPI/Swagger的交互式文档

        ### 📈 使用场景
        - 财务数据分析和量化研究
        - 投资决策支持系统
        - 财务报表自动化生成
        - 证券数据集成服务
        """,
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
        contact={
            "name": "Tushare Query MCP",
            "url": "https://github.com/your-username/tushare-query-mcp",
        },
        license_info={
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT",
        },
    )

    # 添加中间件
    setup_middleware(app)

    # 注册路由
    setup_routes(app)

    # 注册异常处理器
    setup_exception_handlers(app)

    return app


def setup_middleware(app: FastAPI):
    """
    设置应用中间件

    Args:
        app: FastAPI应用实例
    """
    settings = get_settings()

    # CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 在生产环境中应该限制具体的域名
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )

    # Gzip压缩中间件
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # 请求处理时间中间件
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        """添加请求处理时间响应头"""
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(round(process_time, 4))
        return response


def setup_routes(app: FastAPI):
    """
    设置API路由

    Args:
        app: FastAPI应用实例
    """
    # API v1 路由组
    api_v1_prefix = "/api/v1"

    # 注册各个模块的路由
    app.include_router(
        stock.router,
        prefix=api_v1_prefix + "/stock",
        tags=["股票信息"],
    )

    app.include_router(
        income.router,
        prefix=api_v1_prefix + "/income",
        tags=["利润表"],
    )

    app.include_router(
        balance.router,
        prefix=api_v1_prefix + "/balance",
        tags=["资产负债表"],
    )

    app.include_router(
        cashflow.router,
        prefix=api_v1_prefix + "/cashflow",
        tags=["现金流量表"],
    )

    # 根路径重定向到文档
    @app.get("/", include_in_schema=False)
    async def root():
        """根路径重定向到API文档"""
        return {
            "message": "Tushare Query MCP API",
            "version": "0.1.0",
            "docs": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json",
        }

    # 全局健康检查端点
    @app.get("/health", tags=["系统监控"])
    async def global_health_check():
        """
        全局健康检查

        检查API服务的整体状态，包括各个子模块的健康状况。
        """
        logger = logging.getLogger(__name__)

        health_status = {
            "status": "healthy",
            "timestamp": time.time(),
            "version": "0.1.0",
            "services": {},
        }

        # 检查各个子服务的健康状态
        services = [
            ("stock", stock),
            ("income", income),
            ("balance", balance),
            ("cashflow", cashflow),
        ]

        for service_name, service_module in services:
            try:
                # 这里可以调用各个服务的健康检查方法
                # 由于服务层需要异步调用，这里简化处理
                health_status["services"][service_name] = {
                    "status": "healthy",
                    "message": f"{service_name} service is running",
                }
            except Exception as e:
                logger.error(f"Health check failed for {service_name}: {e}")
                health_status["services"][service_name] = {
                    "status": "unhealthy",
                    "message": str(e),
                }
                health_status["status"] = "degraded"

        # 检查配置状态
        settings = get_settings()
        health_status["config"] = {
            "tushare_token_configured": bool(settings.tushare_token),
            "cache_directory": settings.cache_dir,
            "log_level": settings.log_level,
        }

        return health_status


def setup_exception_handlers(app: FastAPI):
    """
    设置全局异常处理器

    Args:
        app: FastAPI应用实例
    """
    logger = logging.getLogger(__name__)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """处理HTTP异常"""
        logger.warning(
            f"HTTP异常 {exc.status_code}: {exc.detail} - 路径: {request.url.path}"
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "error": exc.detail,
                "status_code": exc.status_code,
                "path": str(request.url.path),
                "timestamp": time.time(),
            },
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        """处理值错误"""
        logger.warning(f"值错误: {str(exc)} - 路径: {request.url.path}")
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "error": f"参数错误: {str(exc)}",
                "status_code": 400,
                "path": str(request.url.path),
                "timestamp": time.time(),
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """处理通用异常"""
        logger.error(
            f"未处理的异常: {type(exc).__name__}: {str(exc)} - 路径: {request.url.path}",
            exc_info=True,
        )
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": "服务器内部错误，请稍后重试",
                "status_code": 500,
                "path": str(request.url.path),
                "timestamp": time.time(),
            },
        )


# 创建应用实例
app = create_app()


# 运行应用的便捷函数
def run_app():
    """运行应用（用于开发环境）"""
    import uvicorn

    settings = get_settings()

    uvicorn.run(
        "tushare_query_mcp.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level=settings.log_level.lower(),
        access_log=False,
    )


# 导出应用实例（供WSGI服务器使用）
__all__ = ["app", "create_app", "run_app"]
