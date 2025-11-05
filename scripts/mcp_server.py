"""
Tushare Query MCP 服务器
基于 FastMCP 实现的 Model Context Protocol 服务器，提供中国股票财务数据查询功能
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import List, Optional, Any

from mcp.server.fastmcp import FastMCP
from mcp.types import Tool, TextContent

from tushare_query_mcp.config import get_settings, validate_token
from tushare_query_mcp.services.tushare_datasource import TushareDataSource
from tushare_query_mcp.services.income_service import IncomeService
from tushare_query_mcp.services.balance_service import BalanceService
from tushare_query_mcp.services.cashflow_service import CashFlowService
from tushare_query_mcp.schemas.request import IncomeRequest, BalanceRequest, CashFlowRequest


# 配置日志
logger = logging.getLogger(__name__)

# 全局MCP服务器实例
_mcp_server: Optional[FastMCP] = None


def create_mcp_server() -> FastMCP:
    """
    创建并配置MCP服务器实例

    Returns:
        FastMCP: 配置好的MCP服务器实例

    Raises:
        RuntimeError: 当TUSHARE_TOKEN未配置时
        ValueError: 当token格式无效时
    """
    global _mcp_server

    if _mcp_server is not None:
        return _mcp_server

    # 验证配置
    settings = get_settings()

    if not settings.tushare_token:
        raise RuntimeError("TUSHARE_TOKEN环境变量是必需的")

    if not validate_token(settings.tushare_token):
        raise ValueError("Tushare Token格式无效")

    # 创建FastMCP服务器
    server = FastMCP(
        name="tushare-query-mcp",
        instructions="""
        Tushare财务数据查询MCP服务器，提供以下功能：

        📊 **支持的财务报表**：
        - **利润表** (income)：营收、利润、每股收益等
        - **资产负债表** (balance)：资产、负债、股东权益等
        - **现金流量表** (cashflow)：经营、投资、筹资现金流等

        🔧 **主要功能**：
        - query_stock_financials: 查询指定股票的财务数据
        - 支持自定义字段选择和日期范围过滤
        - 自动缓存机制提升查询效率
        - 完整的错误处理和数据验证

        📈 **使用示例**：
        - 查询贵州茅台最新利润表：ts_code="600519.SH", statement_type="income"
        - 查询指定期间数据：start_date="20240101", end_date="20241231"
        - 自定义字段：fields=["end_date", "total_revenue", "n_income_attr_p"]
        """,
        website_url="https://github.com/your-username/tushare-query-mcp",
        debug=settings.log_level == "DEBUG",
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level
    )

    # 注册工具
    _register_tools(server)

    _mcp_server = server
    logger.info(f"✅ MCP服务器创建成功: {server.name}")
    return server


def _register_tools(server: FastMCP):
    """
    注册所有MCP工具

    Args:
        server: FastMCP服务器实例
    """

    @server.tool()
    async def query_stock_financials(
        ts_code: str,
        statement_type: str,
        fields: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        report_type: Optional[int] = None
    ) -> List[TextContent]:
        """
        查询股票财务数据

        Args:
            ts_code: 股票代码，格式如 "600519.SH"
            statement_type: 报表类型，可选值: "income"（利润表）、"balance"（资产负债表）、"cashflow"（现金流量表）
            fields: 需要返回的字段列表，如未指定则返回默认字段
            start_date: 开始日期，格式：YYYYMMDD（可选）
            end_date: 结束日期，格式：YYYYMMDD（可选）
            report_type: 报表类型：1-合并报表，2-单季合并，3-调整合并报表，4-调整单季合并报表（可选）

        Returns:
            List[TextContent]: 包含查询结果的JSON格式文本内容
        """
        logger.info(f"查询财务数据请求: ts_code={ts_code}, statement_type={statement_type}")

        try:
            # 获取配置
            settings = get_settings()

            # 参数验证
            if not ts_code or not ts_code.strip():
                raise ValueError("股票代码不能为空")

            if not statement_type or not statement_type.strip():
                raise ValueError("报表类型不能为空")

            statement_type = statement_type.lower()
            if statement_type not in ["income", "balance", "cashflow"]:
                raise ValueError("报表类型必须是 'income'、'balance' 或 'cashflow'")

            # 设置默认字段
            if not fields:
                if statement_type == "income":
                    fields = ["end_date", "total_revenue", "n_income_attr_p", "eps"]
                elif statement_type == "balance":
                    fields = ["end_date", "total_assets", "total_equity", "assets_liabs_eq"]
                elif statement_type == "cashflow":
                    fields = ["end_date", "net_cashflows_act", "net_cashflows_inv_act", "net_cashflows_fin_act"]

            # 获取对应的服务实例
            if statement_type == "income":
                service = IncomeService(settings.tushare_token)
                request = IncomeRequest(
                    ts_code=ts_code,
                    fields=fields,
                    start_date=start_date,
                    end_date=end_date,
                    report_type=report_type
                )
                result = await service.get_income_data(request)

            elif statement_type == "balance":
                service = BalanceService(settings.tushare_token)
                request = BalanceRequest(
                    ts_code=ts_code,
                    fields=fields,
                    start_date=start_date,
                    end_date=end_date,
                    report_type=report_type
                )
                result = await service.get_balance_data(request)

            else:  # cashflow
                service = CashFlowService(settings.tushare_token)
                request = CashFlowRequest(
                    ts_code=ts_code,
                    fields=fields,
                    start_date=start_date,
                    end_date=end_date,
                    report_type=report_type
                )
                result = await service.get_cashflow_data(request)

            # 格式化响应 - 处理FinancialDataResponse对象
            if hasattr(result, 'dict'):
                # 如果是Pydantic模型对象
                result_dict = result.dict()
            else:
                # 如果是字典
                result_dict = result

            response_data = {
                "status": result_dict.get("status", "success"),
                "data": result_dict.get("data", []),
                "total_records": result_dict.get("total_records", 0),
                "message": result_dict.get("message", f"{statement_type}查询成功"),
                "from_cache": result_dict.get("from_cache", False),
                "query_time": result_dict.get("query_time", 0),
                "error": result_dict.get("error"),
                "request_params": {
                    "ts_code": ts_code,
                    "statement_type": statement_type,
                    "fields": fields,
                    "start_date": start_date,
                    "end_date": end_date,
                    "report_type": report_type
                },
                "timestamp": datetime.now().isoformat()
            }

            logger.info(f"查询成功: {len(response_data['data'])} 条记录")
            return [TextContent(type="text", text=json.dumps(response_data, ensure_ascii=False, indent=2))]

        except ValueError as e:
            logger.warning(f"参数验证错误: {str(e)}")
            error_response = {
                "status": "error",
                "error": str(e),
                "error_type": "validation_error",
                "request_params": {
                    "ts_code": ts_code,
                    "statement_type": statement_type,
                    "fields": fields,
                    "start_date": start_date,
                    "end_date": end_date,
                    "report_type": report_type
                },
                "timestamp": datetime.now().isoformat()
            }
            return [TextContent(type="text", text=json.dumps(error_response, ensure_ascii=False, indent=2))]

        except Exception as e:
            logger.error(f"查询财务数据失败: {str(e)}", exc_info=True)
            error_response = {
                "status": "error",
                "error": f"查询失败: {str(e)}",
                "error_type": "server_error",
                "request_params": {
                    "ts_code": ts_code,
                    "statement_type": statement_type,
                    "fields": fields,
                    "start_date": start_date,
                    "end_date": end_date,
                    "report_type": report_type
                },
                "timestamp": datetime.now().isoformat()
            }
            return [TextContent(type="text", text=json.dumps(error_response, ensure_ascii=False, indent=2))]

    @server.tool()
    async def get_available_financial_fields(
        statement_type: str,
        ts_code: Optional[str] = None
    ) -> List[TextContent]:
        """
        获取指定报表类型的可用字段列表

        Args:
            statement_type: 报表类型，可选值: "income"、"balance"、"cashflow"
            ts_code: 股票代码，用于获取实际可用字段（可选）

        Returns:
            List[TextContent]: 包含字段列表的JSON格式文本内容
        """
        logger.info(f"获取字段列表请求: statement_type={statement_type}, ts_code={ts_code}")

        try:
            if not statement_type or statement_type not in ["income", "balance", "cashflow"]:
                raise ValueError("报表类型必须是 'income'、'balance' 或 'cashflow'")

            # 预定义的字段映射
            field_mappings = {
                "income": {
                    "basic": ["end_date", "ann_date", "report_type"],
                    "revenue": ["total_revenue", "revenue", "int_income", "prem_income"],
                    "cost": ["oper_cost", "fin_exp", "int_exp", "comm_exp"],
                    "profit": ["operate_profit", "total_profit", "n_income", "n_income_attr_p"],
                    "eps": ["basic_eps", "diluted_eps"],
                    "other": ["update_flag", "comp_type", "end_type"]
                },
                "balance": {
                    "basic": ["end_date", "ann_date", "report_type"],
                    "assets": ["total_assets", "c_cur_assets", "c_ncur_assets", "total_nca"],
                    "liabilities": ["total_liab", "c_cur_liab", "c_ncur_liab"],
                    "equity": ["total_equity", "treasury_stock", "minority_gain"],
                    "specific": ["fix_assets", "cog_inv", "int_assets"],
                    "other": ["update_flag", "comp_type", "end_type"]
                },
                "cashflow": {
                    "basic": ["end_date", "ann_date", "report_type"],
                    "operating": ["net_cashflows_act", "cash_rece_pay", "st_cash_inc"],
                    "investing": ["net_cashflows_inv_act", "invest_cash_rece", "fix_intan_other",
                                 "long_assets", "cfc_invest", "cfc_disp"],
                    "financing": ["net_cashflows_fin_act", "fin_rece_pay", "finance_cash_rece"],
                    "ending": ["c_eq_cash_bal", "ncf_cashflow_e", "exchange_rate"],
                    "other": ["update_flag", "comp_type", "end_type"]
                }
            }

            # 如果提供了股票代码，尝试获取实际可用字段
            actual_fields = None
            if ts_code:
                try:
                    settings = get_settings()
                    if statement_type == "income":
                        service = IncomeService(settings.tushare_token)
                        actual_fields = await service.get_available_fields(ts_code)
                    elif statement_type == "balance":
                        service = BalanceService(settings.tushare_token)
                        actual_fields = await service.get_available_fields(ts_code)
                    else:  # cashflow
                        service = CashFlowService(settings.tushare_token)
                        actual_fields = await service.get_available_fields(ts_code)
                except Exception as e:
                    logger.warning(f"无法获取实际字段列表，使用预定义字段: {str(e)}")

            # 构建响应
            response_data = {
                "statement_type": statement_type,
                "ts_code": ts_code,
                "field_categories": field_mappings.get(statement_type, {}),
                "actual_available_fields": actual_fields,
                "total_predefined_fields": sum(len(fields) for fields in field_mappings.get(statement_type, {}).values()),
                "message": f"获取{statement_type}字段列表成功",
                "timestamp": datetime.now().isoformat()
            }

            return [TextContent(type="text", text=json.dumps(response_data, ensure_ascii=False, indent=2))]

        except Exception as e:
            logger.error(f"获取字段列表失败: {str(e)}", exc_info=True)
            error_response = {
                "status": "error",
                "error": f"获取字段列表失败: {str(e)}",
                "statement_type": statement_type,
                "ts_code": ts_code,
                "timestamp": datetime.now().isoformat()
            }
            return [TextContent(type="text", text=json.dumps(error_response, ensure_ascii=False, indent=2))]

    @server.tool()
    async def validate_financial_fields(
        statement_type: str,
        fields: List[str],
        ts_code: Optional[str] = None
    ) -> List[TextContent]:
        """
        验证指定字段是否存在于对应的财务报表中

        Args:
            statement_type: 报表类型，可选值: "income"、"balance"、"cashflow"
            fields: 要验证的字段列表
            ts_code: 股票代码，用于验证实际可用字段（可选）

        Returns:
            List[TextContent]: 包含验证结果的JSON格式文本内容
        """
        logger.info(f"字段验证请求: statement_type={statement_type}, fields={fields}")

        try:
            if not statement_type or statement_type not in ["income", "balance", "cashflow"]:
                raise ValueError("报表类型必须是 'income'、'balance' 或 'cashflow'")

            if not fields or not isinstance(fields, list):
                raise ValueError("字段列表不能为空且必须是列表格式")

            # 执行验证
            if ts_code:
                # 使用实际股票代码验证
                settings = get_settings()
                if statement_type == "income":
                    service = IncomeService(settings.tushare_token)
                    validation_result = await service.validate_fields(ts_code, fields)
                elif statement_type == "balance":
                    service = BalanceService(settings.tushare_token)
                    validation_result = await service.validate_fields(ts_code, fields)
                else:  # cashflow
                    service = CashFlowService(settings.tushare_token)
                    validation_result = await service.validate_fields(ts_code, fields)
            else:
                # 使用预定义字段验证
                field_mappings = {
                    "income": ["end_date", "ann_date", "report_type", "total_revenue", "revenue",
                              "int_income", "prem_income", "oper_cost", "fin_exp", "int_exp",
                              "comm_exp", "operate_profit", "total_profit", "n_income",
                              "n_income_attr_p", "basic_eps", "diluted_eps"],
                    "balance": ["end_date", "ann_date", "report_type", "total_assets",
                                "c_cur_assets", "c_ncur_assets", "total_nca", "total_liab",
                                "c_cur_liab", "c_ncur_liab", "total_equity", "treasury_stock",
                                "minority_gain", "fix_assets", "cog_inv", "int_assets"],
                    "cashflow": ["end_date", "ann_date", "report_type", "net_cashflows_act",
                                 "cash_rece_pay", "st_cash_inc", "net_cashflows_inv_act",
                                 "invest_cash_rece", "fix_intan_other", "long_assets",
                                 "cfc_invest", "cfc_disp", "net_cashflows_fin_act",
                                 "fin_rece_pay", "finance_cash_rece", "c_eq_cash_bal",
                                 "ncf_cashflow_e", "exchange_rate"]
                }

                valid_fields = field_mappings.get(statement_type, [])
                validation_result = {
                    "valid_fields": [f for f in fields if f in valid_fields],
                    "invalid_fields": [f for f in fields if f not in valid_fields],
                    "total_fields": len(fields),
                    "valid_count": len([f for f in fields if f in valid_fields]),
                    "invalid_count": len([f for f in fields if f not in valid_fields])
                }

            # 构建响应
            response_data = {
                "statement_type": statement_type,
                "ts_code": ts_code,
                "fields_requested": fields,
                "validation_result": validation_result,
                "success_rate": validation_result.get("valid_count", 0) / len(fields) * 100 if fields else 0,
                "message": f"字段验证完成，{validation_result.get('valid_count', 0)}个有效，{validation_result.get('invalid_count', 0)}个无效",
                "timestamp": datetime.now().isoformat()
            }

            return [TextContent(type="text", text=json.dumps(response_data, ensure_ascii=False, indent=2))]

        except Exception as e:
            logger.error(f"字段验证失败: {str(e)}", exc_info=True)
            error_response = {
                "status": "error",
                "error": f"字段验证失败: {str(e)}",
                "statement_type": statement_type,
                "fields": fields,
                "ts_code": ts_code,
                "timestamp": datetime.now().isoformat()
            }
            return [TextContent(type="text", text=json.dumps(error_response, ensure_ascii=False, indent=2))]

    logger.info("✅ 所有MCP工具注册完成")


async def server_health_check() -> dict:
    """
    MCP服务器健康检查

    Returns:
        dict: 健康状态信息
    """
    try:
        settings = get_settings()

        # 检查Tushare数据源连接
        tushare_data_source = TushareDataSource(settings.tushare_token)
        data_source_health = await tushare_data_source.health_check()

        # 检查各服务状态
        services_health = {}
        settings = get_settings()
        for service_name, service_class in [
            ("income", IncomeService),
            ("balance", BalanceService),
            ("cashflow", CashFlowService)
        ]:
            try:
                service = service_class(settings.tushare_token)
                health = await service.health_check()
                services_health[service_name] = health
            except Exception as e:
                services_health[service_name] = {
                    "status": "unhealthy",
                    "message": str(e)
                }

        # 整体健康状态
        overall_status = "healthy"
        unhealthy_services = [name for name, health in services_health.items() if health.get("status") != "healthy"]
        if unhealthy_services:
            overall_status = "degraded"

        health_info = {
            "status": overall_status,
            "server_name": "tushare-query-mcp",
            "version": "0.1.0",
            "data_source": data_source_health,
            "services": services_health,
            "unhealthy_services": unhealthy_services,
            "configuration": {
                "tushare_token_configured": bool(settings.tushare_token),
                "cache_directory": settings.cache_dir,
                "log_level": settings.log_level
            },
            "timestamp": datetime.now().timestamp()
        }

        return health_info

    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}", exc_info=True)
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().timestamp()
        }


def run_mcp_server():
    """
    运行MCP服务器的主入口函数
    """
    try:
        server = create_mcp_server()
        logger.info("🚀 启动Tushare Query MCP服务器...")

        # 通过stdio运行MCP服务器
        import asyncio
        asyncio.run(server.run())

    except Exception as e:
        logger.error(f"启动MCP服务器失败: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    run_mcp_server()


# 导出主要接口
__all__ = [
    "create_mcp_server",
    "run_mcp_server",
    "server_health_check",
    "query_stock_financials",
    "get_available_financial_fields",
    "validate_financial_fields"
]