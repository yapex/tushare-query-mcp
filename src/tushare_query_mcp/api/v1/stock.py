"""
股票信息API路由
提供股票基本信息的RESTful API接口
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ...schemas.request import StockRequest
from ...services.stock_service import StockService
# 导入公共组件
from ..common import (APIResponse, HealthResponse, create_api_response,
                      create_health_response, create_service_dependency,
                      validate_common_params)

# 创建路由器
router = APIRouter()

# 依赖注入：获取StockService实例
get_stock_service = create_service_dependency(StockService)


@router.get("/data", response_model=APIResponse)
async def get_stock_data(
    ts_code: str = Query(..., description="股票代码（如：600519.SH）"),
    fields: str = Query(..., description="字段列表，逗号分隔"),
    start_date: Optional[str] = Query(None, description="开始日期，格式：YYYYMMDD"),
    end_date: Optional[str] = Query(None, description="结束日期，格式：YYYYMMDD"),
    service: StockService = Depends(get_stock_service),
):
    """
    获取股票数据

    Args:
        ts_code: 股票代码
        fields: 需要返回的字段列表，逗号分隔
        start_date: 开始日期（可选）
        end_date: 结束日期（可选）
        service: StockService实例（依赖注入）

    Returns:
        股票数据响应
    """
    # 使用公共验证函数
    field_list = validate_common_params(ts_code, fields, start_date, end_date)

    try:
        # 创建请求对象
        request = StockRequest(
            ts_code=ts_code, fields=field_list, start_date=start_date, end_date=end_date
        )

        # 调用Service层获取数据并转换为API响应
        response = await service.get_stock_data(request)
        return create_api_response(response)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务内部错误：{str(e)}")


@router.get("/health", response_model=HealthResponse)
async def health_check(service: StockService = Depends(get_stock_service)):
    """
    健康检查

    Returns:
        服务健康状态
    """
    try:
        health_status = await service.health_check()
        return create_health_response(health_status)

    except Exception as e:
        return create_health_response(
            {
                "status": "unhealthy",
                "message": f"健康检查失败：{str(e)}",
                "data_source": "error",
                "timestamp": datetime.now().timestamp(),
            }
        )
