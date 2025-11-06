# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## AI Guidance

* Ignore GEMINI.md and GEMINI-*.md files
* Use code-searcher subagent for complex searches and analysis
* Perform multiple operations simultaneously when possible
* Verify solutions before completion
* Use `uv` for dependency management and `uv run` for command execution
* Output content in Chinese
* Prefer editing existing files over creating new ones

## Memory Bank System

This project uses an optimized memory bank system. Key context files:

### Current Context Files
* **CLAUDE-architecture-comprehensive.md** - Complete architecture design and technical decisions
* **CLAUDE-troubleshooting.md** - Common issues and proven solutions
* **CLAUDE-config-variables.md** - Configuration variables reference

### Historical Context (archive/)
* **CLAUDE-activeContext.md** - Project implementation history (8KB)
* **CLAUDE-tdd-plan.md** - TDD implementation plan (12.8KB)

## Project Overview - Tushare MCP API

**✅ 项目状态：生产就绪 (Production Ready)**

Complete FastAPI-based MCP server for querying Chinese stock financial data through Tushare API.

### Key Features
- **13 REST API endpoints** for comprehensive financial data access
- **3 MCP tools** for Claude Code native integration
- **Smart caching system** with time-based persistence
- **DataFrame-safe processing** to avoid boolean ambiguity issues
- **Production-ready** with comprehensive error handling

### Architecture Highlights
- **Layered design**: API → Service → DataSource → Tushare API
- **Smart field selection** to optimize token usage
- **Async processing** for high performance
- **Comprehensive testing** (300+ tests, >90% coverage)

### Quick Start
```bash
# Start all services
uv run poe start

# API docs: http://localhost:8000/docs
# Health check: http://localhost:8000/health
```

For detailed architecture information, see **CLAUDE-architecture-comprehensive.md**.

## 🚀 快速使用指南

### 启动服务
```bash
# 启动所有服务 (FastAPI + MCP)
uv run poe start

# API 文档: http://localhost:8000/docs
# 健康检查: http://localhost:8000/health
```

### 项目管理命令
- `uv run poe stop` - 停止服务
- `uv run poe restart` - 重启服务
- `uv run poe test` - 运行测试
- `uv run poe format` - 格式化代码
- `uv run poe lint` - 代码检查

### MCP 工具
- `query_stock_financials` - 查询财务数据
- `get_available_financial_fields` - 获取字段列表
- `validate_financial_fields` - 验证字段

### 项目约定
- 源代码位于 `src/` 目录
- 脚本文件位于 `scripts/` 目录
- 使用 `uv run` 执行所有命令