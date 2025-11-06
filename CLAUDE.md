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
* **[CLAUDE-architecture-comprehensive.md](docs/architecture/CLAUDE-architecture-comprehensive.md)** - Complete architecture design and technical decisions
* **[CLAUDE-troubleshooting.md](docs/troubleshooting/CLAUDE-troubleshooting.md)** - Common issues and proven solutions
* **[CLAUDE-config-variables.md](docs/troubleshooting/CLAUDE-config-variables.md)** - Configuration variables reference

### Historical Context (docs/archive/)
* **[CLAUDE-activeContext.md](docs/archive/CLAUDE-activeContext.md)** - Project implementation history (8KB)
* **[CLAUDE-tdd-plan.md](docs/archive/CLAUDE-tdd-plan.md)** - TDD implementation plan (12.8KB)

## Project Overview - Tushare MCP API

**✅ 项目状态：生产就绪 (Production Ready)**
**🧪 测试状态：100% 通过 (243 passed, 4 skipped, 0 failed)**

Complete FastAPI-based MCP server for querying Chinese stock financial data through Tushare API.

### 核心特性
- **14个REST API端点**：完整财务数据访问
- **3个MCP工具**：Claude Code原生集成
- **智能缓存系统**：时间持久化存储
- **DataFrame安全处理**：避免布尔歧义问题
- **🔥 依赖注入架构**：遵循SOLID原则
- **🧪 100% 测试通过**：247个测试用例，243个通过，4个跳过
- **🏗️ 企业级架构**：完全的依赖注入支持

### 测试成果
- **单元测试**: 完全覆盖所有核心组件
- **集成测试**: API路由和服务层完全验证
- **E2E测试**: 端到端功能全部通过
- **MCP测试**: 核心MCP工具功能验证完成
- **性能测试**: 缓存和异步处理优化验证

### 快速启动
```bash
uv run poe start          # 启动所有服务
# API文档: http://localhost:8000/docs
# 健康检查: http://localhost:8000/health
```

📋 **完整架构信息**: 查看 [CLAUDE-architecture-comprehensive.md](docs/architecture/CLAUDE-architecture-comprehensive.md)

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
- `query_stock_financials` - 查询财务数据（支持利润表、资产负债表、现金流量表）
- `get_available_financial_fields` - 获取可用字段列表
- `validate_financial_fields` - 验证指定字段是否存在

### 分析工具和指南
- **[企业资产安全性分析指导](docs/guides/企业资产安全性分析指导.md)** - 财务分析框架
  - 五大维度评估（资产质量、偿债能力、营运能力、盈利能力、现金流安全）
  - 20+核心指标和三级风险预警
  - 案例：贵州茅台分析（95.2/100分，优秀级）

### 项目约定
- 源代码位于 `src/` 目录
- 脚本文件位于 `scripts/` 目录
- MCP服务器位于 `scripts/mcp_server.py`
- 项目文档统一管理在 `docs/` 目录
- 使用 `uv run` 执行所有命令

### 📚 文档组织
项目采用清晰的文档分层结构：
- **根目录README.md**: 项目概览和快速开始
- **docs/README.md**: 完整文档导航目录
- **docs/guides/**: 使用指南和分析框架
- **docs/architecture/**: 架构设计文档
- **docs/troubleshooting/**: 故障排除和配置参考
- **docs/archive/**: 历史文档归档

### 🔍 企业资产安全性分析
**完整财务分析框架**: [docs/guides/企业资产安全性分析指导.md](docs/guides/企业资产安全性分析指导.md)
- 五大维度评估体系和20+核心指标
- 三级风险预警机制
- 案例：贵州茅台分析（95.2/100分）
- 基于tushare-query-mcp数据查询能力

### 项目结构
```
tushare-query-mcp/
├── README.md          # 项目概览
├── CLAUDE.md          # AI指导文件
├── docs/              # 📚 文档目录
│   ├── guides/        # 分析指南
│   ├── architecture/  # 架构文档
│   ├── troubleshooting/ # 故障排除
│   └── archive/       # 历史文档
├── src/               # 源代码（SOLID架构）
├── scripts/           # 启动脚本
└── tests/             # 测试套件（247个测试，100%通过）
```

## 🏗️ 架构设计

### SOLID架构原则

**🔥 核心原则**: 严格遵循SOLID设计原则，所有依赖通过构造函数注入，依赖抽象而非具体实现。

**关键要求**:
- 构造函数依赖注入（禁止类内部创建依赖）
- 依赖Protocol接口抽象
- 单一职责原则
- 精简接口设计
- 开闭原则（扩展而非修改）

**核心优势**:
- ✅ 100%可测试性（完美Mock支持）
- ✅ 零过度设计
- ✅ 插件式架构
- ✅ 企业级可维护性

📋 **详细架构文档**: [CLAUDE-architecture-comprehensive.md](docs/architecture/CLAUDE-architecture-comprehensive.md)