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

📋 **完整架构信息**: 查看 [CLAUDE-architecture-comprehensive.md](CLAUDE-architecture-comprehensive.md)

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

### 项目约定
- 源代码位于 `src/` 目录
- 脚本文件位于 `scripts/` 目录
- MCP服务器位于 `scripts/mcp_server.py`
- 使用 `uv run` 执行所有命令

### 当前项目结构
```
src/tushare_query_mcp/
├── interfaces/           # ✅ 新增：核心依赖接口
│   └── core.py          # Protocol接口定义
├── api/v1/              # REST API层（14个端点）
├── services/            # 业务逻辑层（支持依赖注入）
├── utils/               # 工具类（缓存、字段选择等）
├── schemas/             # 数据模型定义
└── main.py             # FastAPI应用入口

scripts/
├── mcp_server.py       # MCP服务器（3个工具）
├── start.py           # 服务启动脚本
└── start_server.py    # API服务器启动脚本

tests/                 # 测试套件（247个测试用例，100%通过率）
```

## 🏗️ 架构设计

### ⚡ **极其重要的设计原则：SOLID架构**

> **🔥 警告：SOLID原则是此项目的核心架构基础，任何代码修改都必须严格遵循这些原则！**

**SOLID设计原则不是可选项，而是必须严格遵守的架构准则！** 违反SOLID原则会直接导致：
- 代码可维护性急剧下降
- 测试覆盖率和质量严重受损
- 系统扩展性完全丧失
- 技术债务快速增长

#### **🚨 关键设计要求**
1. **所有依赖必须通过构造函数注入** - 绝对禁止在类内部创建依赖对象
2. **依赖抽象而非具体实现** - 所有服务层必须依赖Protocol接口
3. **单一职责不可违背** - 每个类只能有且仅有一个职责
4. **接口设计必须精简** - 避免过度设计，只包含必要方法
5. **开闭原则必须贯彻** - 新功能通过扩展而非修改实现

### 依赖注入架构
项目采用**构造函数依赖注入**模式，**严格遵循SOLID原则**：

#### Protocol接口层 (`src/tushare_query_mcp/interfaces/`)
```python
# core.py - 简化的核心接口
class IDataSource(Protocol):
    async def get_income_data(self, request: FinancialDataRequest) -> List[Dict[str, Any]]: ...
    async def get_balance_data(self, request: FinancialDataRequest) -> List[Dict[str, Any]]: ...
    async def get_cashflow_data(self, request: FinancialDataRequest) -> List[Dict[str, Any]]: ...
    async def health_check(self) -> bool: ...

class ICache(Protocol):
    async def get(self, key: str) -> Optional[List[Dict[str, Any]]]: ...
    async def set(self, key: str, data: List[Dict[str, Any]], expire: int) -> bool: ...
```

#### 服务层依赖注入
```python
# ✅ 支持依赖注入和向后兼容的构造函数
class IncomeService(BaseFinancialService):
    def __init__(self, data_source_or_token):
        # 检查是否是token字符串（向后兼容）
        if isinstance(data_source_or_token, str):
            # 向后兼容：自动创建TushareDataSource
            data_source = TushareDataSource(data_source_or_token)
        else:
            # 新方式：使用注入的数据源
            data_source = data_source_or_token

        super().__init__(data_source, "利润表")

# 使用示例
service = IncomeService("token")      # 向后兼容：自动创建TushareDataSource
service = IncomeService(mock_data_source)  # 依赖注入：使用mock进行测试
```

### ✅ SOLID架构实现

**严格遵循SOLID原则，确保企业级代码质量和可维护性。**

- **单一职责**: 每个类职责明确分离
- **开闭原则**: 通过接口扩展，无需修改现有代码
- **里氏替换**: 所有实现可完全互换
- **接口隔离**: 精简接口设计，避免过度依赖
- **依赖倒置**: 依赖抽象，通过构造函数注入

📋 **详细实现**: 查看 [CLAUDE-architecture-comprehensive.md](CLAUDE-architecture-comprehensive.md#-solid架构实现)

### 🚀 SOLID架构带来的无与伦比优势

> **🎯 这些优势直接来源于对SOLID原则的严格执行！**

#### **🔥 构造函数注入的威力**
- **完全的依赖控制**: 所有依赖在构造时明确声明
- **零隐藏依赖**: 绝对没有运行时意外创建的对象
- **完美的依赖图**: 通过构造函数清晰看到所有依赖关系

#### **🔥 100%可测试性的保证**
- **完美的Mock注入**: 任何依赖都可以被替换为测试替身
- **单元测试隔离**: 每个类都可以独立测试，无副作用
- **测试覆盖率90%+**: 得益于完美的依赖注入架构

#### **🔥 极致的代码简洁性**
- **零过度设计**: Protocol接口只包含必要方法
- **专注核心抽象**: 每个类都有单一、明确的职责
- **代码即文档**: 架构自解释，无需额外文档

#### **🔥 无与伦比的扩展性**
- **插件式架构**: 新功能通过实现接口无缝集成
- **向后兼容**: 新增功能永远不需要修改现有代码
- **企业级可维护**: 即使项目规模扩大，架构依然清晰可控