# QWEN.md - 项目工作指南

## 核心原则

Qwen Code 在本仓库工作时，请遵循以下原则：

1. **直接参考CLAUDE文档** - 所有项目相关的最新信息都在CLAUDE文档中
2. **避免忽略CLAUDE相关文件** - 这些文件包含最新的项目上下文
3. **作为项目工作的"路书"** - 引导访问真实的信息源

## 关键文档路径

### 项目核心文档（必须直接阅读）
- `CLAUDE.md` - 项目基本配置和约定
- `docs/README.md` - 完整文档导航目录
- `docs/architecture/CLAUDE-architecture-comprehensive.md` - 完整架构设计和技术决策
- `docs/troubleshooting/CLAUDE-troubleshooting.md` - 常见问题和解决方案
- `docs/troubleshooting/CLAUDE-config-variables.md` - 配置变量参考

### 分析工具和指南
- `docs/guides/企业资产安全性分析指导.md` - 企业资产安全性分析框架
  - 五大维度评估体系（资产质量、偿债能力、营运能力、盈利能力、现金流安全）
  - 20+核心指标和三级风险预警机制
  - 贵州茅台分析案例（95.2/100分）

### 项目状态概览
- **项目状态**: 生产就绪 (Production Ready)
- **测试状态**: 247个测试用例，100%通过率
- **架构**: SOLID依赖注入设计
- **服务**: FastAPI REST API + MCP集成

### 重要：保持信息同步
每当开始项目工作时，请先检查以上CLAUDE文档的最新内容，确保获取最新的项目状态、架构变化和问题解决方案。

## 快速操作参考

### 常用命令
```bash
# 服务管理
uv run poe start     # 启动所有服务
uv run poe stop      # 停止服务
uv run poe restart   # 重启服务

# 开发和测试
uv run poe test      # 运行测试
uv run poe format    # 格式化代码
uv run poe lint      # 代码检查
```

### MCP工具
- `query_stock_financials` - 查询财务数据
- `get_available_financial_fields` - 获取可用字段
- `validate_financial_fields` - 验证字段有效性

## 重要提醒

为了获取项目的最新状态（包括架构变更、问题解决方案、配置更新等），请直接查阅相应的CLAUDE文档。这些文档是项目知识的权威来源，QWEN.md仅作为访问这些文档的"路书"存在。

**注意**: 本文档仅作为导航索引，具体的项目信息、技术细节和操作指南请参考上述具体文档路径。
