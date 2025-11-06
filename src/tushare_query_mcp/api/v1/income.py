"""
利润表API路由
提供利润表数据的RESTful API接口
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ...schemas.request import IncomeRequest
from ...services.income_service import IncomeService
# 导入公共组件
from ..common import (APIResponse, FieldsResponse, HealthResponse,
                      ValidationResponse, create_api_response,
                      create_fields_response, create_health_response,
                      create_service_dependency, create_validation_response,
                      validate_common_params, validate_report_type)

# 创建路由器
router = APIRouter()


# 导出依赖项以支持测试
__all__ = ["router", "get_income_service"]

# 依赖注入：获取IncomeService实例
def get_income_service():
    """获取IncomeService实例，支持依赖注入和测试覆盖"""
    from tushare_query_mcp.config import get_settings
    settings = get_settings()
    return IncomeService(settings.tushare_token)


@router.get("/data", response_model=APIResponse)
async def get_income_data(
    ts_code: str = Query(..., description="股票代码（如：600519.SH）"),
    fields: str = Query(
        ..., description="字段列表，逗号分隔（如：end_date,total_revenue）"
    ),
    start_date: Optional[str] = Query(None, description="开始日期，格式：YYYYMMDD"),
    end_date: Optional[str] = Query(None, description="结束日期，格式：YYYYMMDD"),
    report_type: Optional[str] = Query(
        None, description="报告类型：1-合并报表，2-母公司报表"
    ),
    service: IncomeService = Depends(get_income_service),
):
    """
    获取利润表数据

    Args:
        ts_code: 股票代码
        fields: 需要返回的字段列表，逗号分隔
        start_date: 开始日期（可选）
        end_date: 结束日期（可选）
        report_type: 报告类型（可选）
        service: IncomeService实例（依赖注入）

    Returns:
        利润表数据响应
    """
    # 使用公共验证函数
    field_list = validate_common_params(ts_code, fields, start_date, end_date)
    validate_report_type(report_type)

    try:
        # 创建请求对象
        request = IncomeRequest(
            ts_code=ts_code,
            fields=field_list,
            start_date=start_date,
            end_date=end_date,
            report_type=report_type,
        )

        # 调用Service层获取数据并转换为API响应
        response = await service.get_income_data(request)
        return create_api_response(response)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务内部错误：{str(e)}")


@router.get("/health", response_model=HealthResponse)
async def health_check(service: IncomeService = Depends(get_income_service)):
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


@router.get("/fields", response_model=FieldsResponse)
async def get_available_fields(
    ts_code: str = Query(..., description="股票代码"),
    start_date: Optional[str] = Query(None, description="开始日期，格式：YYYYMMDD"),
    end_date: Optional[str] = Query(None, description="结束日期，格式：YYYYMMDD"),
    service: IncomeService = Depends(get_income_service),
):
    """
    获取可用字段列表

    Args:
        ts_code: 股票代码
        start_date: 开始日期（可选）
        end_date: 结束日期（可选）
        service: IncomeService实例

    Returns:
        可用字段列表
    """
    if not ts_code:
        raise HTTPException(status_code=422, detail="股票代码不能为空")

    try:
        fields = await service.get_available_fields(ts_code, start_date, end_date)
        return create_fields_response(fields)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取字段列表失败：{str(e)}")


@router.post("/validate", response_model=ValidationResponse)
async def validate_fields(
    ts_code: str = Query(..., description="股票代码"),
    fields: List[str] = Query(..., description="要验证的字段列表"),
    start_date: Optional[str] = Query(None, description="开始日期，格式：YYYYMMDD"),
    end_date: Optional[str] = Query(None, description="结束日期，格式：YYYYMMDD"),
    service: IncomeService = Depends(get_income_service),
):
    """
    验证字段是否存在

    Args:
        ts_code: 股票代码
        fields: 要验证的字段列表
        start_date: 开始日期（可选）
        end_date: 结束日期（可选）
        service: IncomeService实例

    Returns:
        字段验证结果
    """
    if not ts_code:
        raise HTTPException(status_code=422, detail="股票代码不能为空")

    if not fields:
        raise HTTPException(status_code=422, detail="字段列表不能为空")

    try:
        validation_result = await service.validate_fields(
            ts_code, fields, start_date, end_date
        )
        return create_validation_response(validation_result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"字段验证失败：{str(e)}")


# 注意：异常处理器需要在FastAPI应用层面注册，而不是在APIRouter层面
# 这些处理器将在main.py中注册
