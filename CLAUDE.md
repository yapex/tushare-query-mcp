# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## AI Guidance

* Ignore GEMINI.md and GEMINI-*.md files
* To save main context space, for code searches, inspections, troubleshooting or analysis, use code-searcher subagent where appropriate - giving the subagent full context background for the task(s) you assign it.
* After receiving tool results, carefully reflect on their quality and determine optimal next steps before proceeding. Use your thinking to plan and iterate based on this new information, and then take the best next action.
* For maximum efficiency, whenever you need to perform multiple independent operations, invoke all relevant tools simultaneously rather than sequentially.
* Before you finish, please verify your solution
* Do what has been asked; nothing more, nothing less.
* NEVER create files unless they're absolutely necessary for achieving your goal.
* ALWAYS prefer editing an existing file to creating a new one.
* NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.
* When you update or modify core context files, also update markdown documentation and memory bank
* When asked to commit changes, exclude CLAUDE.md and CLAUDE-*.md referenced memory bank system files from any commits. Never delete these files.
* 使用 uv 管理项目依赖，使用 uv run 运行 python 代码
* 以中文输出内容

## Memory Bank System

This project uses a structured memory bank system with specialized context files. Always check these files for relevant information before starting work:

### Core Context Files

* **CLAUDE-activeContext.md** - Current session state, goals, and progress (if exists)
* **CLAUDE-patterns.md** - Established code patterns and conventions (if exists)
* **CLAUDE-decisions.md** - Architecture decisions and rationale (if exists)
* **CLAUDE-troubleshooting.md** - Common issues and proven solutions (if exists)
* **CLAUDE-config-variables.md** - Configuration variables reference (if exists)
* **CLAUDE-temp.md** - Temporary scratch pad (only read when referenced)

**Important:** Always reference the active context file first to understand what's currently being worked on and maintain session continuity.

### Memory Bank System Backups

When asked to backup Memory Bank System files, you will copy the core context files above and @.claude settings directory to directory @/path/to/backup-directory. If files already exist in the backup directory, you will overwrite them.

## Project Overview - Tushare MCP API

**✅ 项目状态：生产就绪 (Production Ready)**

This project provides a complete FastAPI-based MCP (Model Context Protocol) server for querying Chinese stock financial data through the Tushare API. The project has been fully implemented, tested, and is ready for production use.

### Development Patterns

This project follows Test-Driven Development (TDD) methodology with:
- Comprehensive test suite (300+ tests)
- Mock testing for isolation
- Real API validation
- Clean architecture with separation of concerns
- High test coverage (>90%)

**For more details, see CLAUDE-activeContext.md and CLAUDE-decisions.md**

## 🚀 项目架构和使用方式

### 核心组件
- **FastAPI REST API 服务器** (`src/tushare_query_mcp/main.py`)
- **MCP 服务器** (`scripts/mcp_server.py`)
- **服务层**: IncomeService, BalanceService, CashFlowService
- **数据源**: TushareDataSource (基于 Tushare API)
- **配置管理**: 基于 Pydantic Settings

### 🛠️ 服务管理 (Poe Tasks)

项目现在支持完整的服务管理命令：

**启动服务:**
```bash
# 启动所有服务 (FastAPI + MCP)
uv run poe start

# 或手动启动 FastAPI
uv run uvicorn tushare_query_mcp.main:app --reload
```

**停止服务:**
```bash
# 停止所有相关服务
uv run poe stop
```

**重启服务:**
```bash
# 重启所有服务
uv run poe restart
```

**其他管理命令:**
```bash
# 格式化代码
uv run poe format

# 代码检查
uv run poe lint

# 运行测试
uv run poe test

# 运行测试并生成覆盖率报告
uv run poe test-cov
```

### 🌐 访问地址

**API 文档:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- 健康检查: http://localhost:8000/health

### 🔧 MCP 服务器使用

```python
from scripts.mcp_server import create_mcp_server

# 创建服务器实例
server = create_mcp_server()

# 调用工具示例
result = await server.call_tool('query_stock_financials', {
    'ts_code': '600519.SH',
    'statement_type': 'income',
    'fields': ['end_date', 'total_revenue', 'n_income_attr_p']
})
```

### 📋 MCP 工具列表
- `query_stock_financials` - 查询股票财务数据 (支持 income/balance/cashflow)
- `get_available_financial_fields` - 获取可用字段列表
- `validate_financial_fields` - 验证字段有效性

### 📊 项目特性
- **13个 REST API 端点** - 完整的财务数据查询接口
- **3个 MCP 工具** - Claude Code 原生集成
- **智能缓存系统** - 基于时间的持久化缓存
- **双协议支持** - REST API + MCP 协议
- **生产就绪** - 完整的错误处理和监控

### 🎯 项目约定
- 脚本类文件统一放在 `scripts/` 目录
- 源代码从 `src/` 子目录开始，导入不包含 `src.`
- 使用 `uv run` 管理所有命令
- 优先使用 `uv run poe start/stop/restart` 管理服务