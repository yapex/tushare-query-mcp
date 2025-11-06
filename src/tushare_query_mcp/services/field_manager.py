"""
字段管理器服务 - 结合 stock_schema.toml 和 API 动态字段信息
"""

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set

import toml


@dataclass
class FieldInfo:
    """字段信息数据类"""

    name: str
    description: str
    type: str
    available: bool = True
    category: str = ""
    source: str = "schema"  # schema, api_only, both


class FieldManager:
    """字段管理器 - 整合 Schema 定义和 API 可用性信息"""

    def __init__(self, schema_path: str = "stock_schema.toml"):
        self.schema_path = Path(schema_path)
        self._schema_cache = None
        self._category_rules = self._init_category_rules()
        self.logger = logging.getLogger(__name__)

    def _init_category_rules(self) -> Dict[str, List[str]]:
        """初始化字段分类规则"""
        return {
            "revenue": [
                "revenue",
                "income",
                "earn",
                "profit",
                "gain",
                "premium",
                "comm_income",
                "n_commis_income",
                "oth_b_income",
                "int_income",
                "fv_value_chg_gain",
                "invest_income",
                "forex_gain",
                "non_oper_income",
            ],
            "cost": [
                "cost",
                "exp",
                "expense",
                "loss",
                "payout",
                "impair",
                "write",
                "oper_cost",
                "fin_exp",
                "int_exp",
                "comm_exp",
                "biz_tax",
                "sell_exp",
                "admin_exp",
                "assets_impair_loss",
                "oper_exp",
                "rd_exp",
            ],
            "assets": [
                "asset",
                "receiv",
                "invent",
                "prepay",
                "invest",
                "fix",
                "cip",
                "intang",
                "goodwill",
                "depos",
                "cash",
                "trading",
                "avail",
                "lt_rec",
                "total_cur_assets",
                "total_nca",
                "fix_assets",
                "intan_assets",
            ],
            "liabilities": [
                "liab",
                "payable",
                "borrow",
                "debt",
                "loan",
                "bond",
                "provision",
                "accrual",
                "defer",
                "st_borr",
                "lt_borr",
                "notes_payable",
                "acct_payable",
                "taxes_payable",
                "total_cur_liab",
                "total_ncl",
                "contract_liab",
            ],
            "equity": [
                "equity",
                "share",
                "capital",
                "reserve",
                "surplus",
                "retained",
                "treasury",
                "minority",
                "total_hldr_eqy",
                "cap_rese",
                "undistr_porfit",
            ],
            "cashflow": [
                "cash",
                "flow",
                "n_cashflow",
                "c_fr",
                "c_paid",
                "st_cash",
                "free_cashflow",
                "invest_cash",
                "finance_cash",
                "disbursement",
                "receipt",
            ],
            "basic": [
                "end_date",
                "ann_date",
                "report_type",
                "comp_type",
                "end_type",
                "update_flag",
                "ts_code",
                "f_ann_date",
            ],
        }

    def _load_schema(self) -> Dict:
        """加载并缓存 Schema 数据"""
        if self._schema_cache is None:
            if not self.schema_path.exists():
                raise FileNotFoundError(f"Schema file not found: {self.schema_path}")

            with open(self.schema_path, "r", encoding="utf-8") as f:
                self._schema_cache = toml.load(f)
        return self._schema_cache

    def get_schema_fields(self, statement_type: str) -> Dict[str, FieldInfo]:
        """
        从 Schema 获取字段定义

        Args:
            statement_type: 报表类型 (income, balance, cashflow)

        Returns:
            Dict[str, FieldInfo]: 字段名到字段信息的映射
        """
        try:
            schema = self._load_schema()
            table_mapping = {
                "income": "income",
                "balance": "balance_sheet",
                "cashflow": "cash_flow",
            }

            if statement_type not in table_mapping:
                raise ValueError(f"Unsupported statement type: {statement_type}")

            table_name = table_mapping[statement_type]
            table_schema = schema[table_name]

            fields = {}
            for col in table_schema["columns"]:
                field_info = FieldInfo(
                    name=col["name"],
                    description=col["desc"],
                    type=col["type"],
                    category=self._infer_category(col["name"]),
                    source="schema",
                )
                fields[col["name"]] = field_info

            return fields

        except Exception as e:
            self.logger.error(
                f"Failed to load schema fields for {statement_type}: {str(e)}"
            )
            return {}

    def get_enhanced_fields(
        self, statement_type: str, api_available_fields: List[str]
    ) -> Dict[str, FieldInfo]:
        """
        结合 Schema 和 API 数据返回增强字段信息

        Args:
            statement_type: 报表类型
            api_available_fields: API 返回的可用字段列表

        Returns:
            Dict[str, FieldInfo]: 增强的字段信息
        """
        schema_fields = self.get_schema_fields(statement_type)
        api_field_set = set(api_available_fields)

        result = {}

        # 处理所有字段
        all_field_names = set(schema_fields.keys()) | api_field_set

        for field_name in all_field_names:
            if field_name in schema_fields:
                # Schema 中定义的字段
                field_info = schema_fields[field_name]
                field_info.available = field_name in api_field_set
                field_info.source = (
                    "both" if field_name in api_field_set else "schema_only"
                )
                result[field_name] = field_info
            else:
                # API 独有字段
                result[field_name] = FieldInfo(
                    name=field_name,
                    description=self._generate_description(field_name),
                    type="UNKNOWN",
                    available=True,
                    category=self._infer_category(field_name),
                    source="api_only",
                )

        return result

    def _infer_category(self, field_name: str) -> str:
        """
        根据字段名推断分类

        Args:
            field_name: 字段名称

        Returns:
            str: 字段分类
        """
        field_name_lower = field_name.lower()

        # 按优先级匹配分类
        for category, keywords in self._category_rules.items():
            for keyword in keywords:
                if keyword in field_name_lower:
                    return category

        return "other"

    def _generate_description(self, field_name: str) -> str:
        """
        为 API 独有字段生成描述

        Args:
            field_name: 字段名称

        Returns:
            str: 生成的描述
        """
        # 常见字段的描述映射
        description_map = {
            "continued_net_profit": "持续经营净利润",
            "free_cashflow": "企业自由现金流量",
            "credit_impa_loss": "信用减值损失",
            "use_right_asset_dep": "使用权资产折旧",
            "oth_loss_asset": "其他资产减值损失",
            "end_bal_cash": "现金的期末余额",
            "beg_bal_cash": "现金的期初余额",
            "end_bal_cash_equ": "现金等价物的期末余额",
            "beg_bal_cash_equ": "现金等价物的期初余额",
            "im_net_cashflow_oper_act": "经营活动产生的现金流量净额(间接法)",
            "im_n_incr_cash_equ": "现金及现金等价物净增加额(间接法)",
            "net_dism_capital_add": "拆出资金净增加额",
            "net_cash_rece_sec": "代理买卖证券收到的现金净额",
            "uncon_invest_loss": "未确认的投资损失",
            "prov_depr_assets": "资产减值准备",
            "depr_fa_coga_dpba": "固定资产折旧、油气资产折耗、生产性生物资产折旧",
            "amort_intang_assets": "无形资产摊销",
            "lt_amort_deferred_exp": "长期待摊费用摊销",
            "loss_disp_fiolta": "处置固定资产、无形资产和其他长期资产的损失",
            "loss_scr_fa": "固定资产报废损失",
            "loss_fv_chg": "公允价值变动损失",
            "invest_loss": "投资损失",
            "decr_def_inc_tax_assets": "递延所得税资产减少",
            "incr_def_inc_tax_liab": "递延所得税负债增加",
            "decr_inventories": "存货的减少",
            "decr_oper_payable": "经营性应收项目的减少",
            "incr_oper_payable": "经营性应付项目的增加",
            "conv_debt_into_cap": "债务转为资本",
            "conv_copbonds_due_within_1y": "一年内到期的可转换公司债券",
            "fa_fnc_leases": "融资租入固定资产",
        }

        # 直接查找
        if field_name in description_map:
            return description_map[field_name]

        # 基于规则的生成
        if field_name.startswith("st_"):
            return f"短期{field_name[3:]}"
        elif field_name.startswith("lt_"):
            return f"长期{field_name[3:]}"
        elif field_name.startswith("n_"):
            return f"净{field_name[2:]}"
        elif field_name.startswith("c_"):
            return f"现金{field_name[2:]}"
        elif field_name.endswith("_inc"):
            return f"{field_name[:-4]}增加额"
        elif field_name.endswith("_dec"):
            return f"{field_name[:-4]}减少额"
        elif "pay" in field_name:
            return f"支付{field_name.replace('pay', '')}"
        elif "receiv" in field_name:
            return f"应收{field_name.replace('receiv', '')}"
        elif "payable" in field_name:
            return f"应付{field_name.replace('payable', '')}"
        else:
            # 简单的驼峰转中文
            return f"字段 {field_name}"

    def get_fields_by_category(
        self,
        statement_type: str,
        api_available_fields: List[str] = None,
        only_available: bool = True,
    ) -> Dict[str, List[str]]:
        """
        按分类获取字段列表

        Args:
            statement_type: 报表类型
            api_available_fields: API 可用字段列表
            only_available: 是否只返回可用字段

        Returns:
            Dict[str, List[str]]: 按分类组织的字段列表
        """
        if api_available_fields is None:
            # 如果没有提供 API 字段，返回 Schema 字段
            enhanced_fields = self.get_schema_fields(statement_type)
        else:
            enhanced_fields = self.get_enhanced_fields(
                statement_type, api_available_fields
            )

        categories = {}
        for name, info in enhanced_fields.items():
            if not only_available or info.available:
                category = info.category
                if category not in categories:
                    categories[category] = []
                categories[category].append(name)

        return categories

    def validate_fields(
        self,
        statement_type: str,
        fields: List[str],
        api_available_fields: List[str] = None,
    ) -> Dict:
        """
        验证字段有效性

        Args:
            statement_type: 报表类型
            fields: 要验证的字段列表
            api_available_fields: API 可用字段列表

        Returns:
            Dict: 验证结果
        """
        if api_available_fields is None:
            enhanced_fields = self.get_schema_fields(statement_type)
        else:
            enhanced_fields = self.get_enhanced_fields(
                statement_type, api_available_fields
            )

        valid_fields = []
        invalid_fields = []
        field_details = {}

        for field_name in fields:
            if field_name in enhanced_fields and enhanced_fields[field_name].available:
                valid_fields.append(field_name)
                field_info = enhanced_fields[field_name]
                field_details[field_name] = {
                    "name": field_info.name,
                    "description": field_info.description,
                    "type": field_info.type,
                    "category": field_info.category,
                    "source": field_info.source,
                }
            else:
                invalid_fields.append(field_name)

        return {
            "valid_fields": valid_fields,
            "invalid_fields": invalid_fields,
            "total_fields": len(fields),
            "valid_count": len(valid_fields),
            "invalid_count": len(invalid_fields),
            "field_details": field_details,
        }
