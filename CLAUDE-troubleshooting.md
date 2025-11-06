# 常见问题和解决方案

## 🚨 启动问题

### 问题：服务器无法启动
**症状**:
```
uv run uvicorn tushare_query_mcp.main:app --reload
# 报错：ModuleNotFoundError: No module named 'tushare_query_mcp'
```

**解决方案**:
1. 检查是否在项目根目录
2. 确认已安装依赖：`uv sync`
3. 验证 `pyproject.toml` 配置正确

**验证方法**:
```bash
uv run python -c "from tushare_query_mcp.main import app; print('✅ 导入成功')"
```

### 问题：端口被占用
**症状**:
```
Address already in use
```

**解决方案**:
1. 更换端口：`uv run uvicorn tushare_query_mcp.main:app --port 8080`
2. 找到并停止占用端口的进程：
   ```bash
   lsof -ti:8000 | xargs kill -9
   ```

### 问题：TUSHARE_TOKEN 未配置
**症状**:
```
RuntimeError: TUSHARE_TOKEN环境变量是必需的
```

**解决方案**:
1. 创建 `.env` 文件：
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，添加真实的 token
   ```
2. 或直接设置环境变量：
   ```bash
   export TUSHARE_TOKEN=your_token_here
   ```

## 🔌 API 调用问题

### 问题：API 返回 500 错误
**症状**: API 端点返回服务器内部错误

**诊断步骤**:
1. 检查服务器日志中的详细错误信息
2. 访问健康检查端点：`http://localhost:8000/health`
3. 验证 Tushare token 有效性

**常见原因**:
- Tushare API token 无效或过期
- 网络连接问题
- API 调用频率超限

### 问题：数据格式错误
**症状**:
```
'str' object has no attribute 'value'
```

**解决方案**:
这通常是 Pydantic 模型验证问题，检查：
1. 请求参数格式是否正确
2. 日期格式是否为 YYYYMMDD
3. 股票代码格式是否正确（如 600519.SH）

### 问题：缓存相关问题
**症状**: 数据不更新或缓存错误

**解决方案**:
1. 清理缓存：
   ```bash
   rm -rf ./.cache
   ```
2. 检查缓存目录权限
3. 调整缓存 TTL 配置

## 🔧 MCP 服务器问题

### 问题：MCP 工具调用失败
**症状**: MCP 工具返回错误或无响应

**诊断步骤**:
1. 测试基础服务器创建：
   ```python
   from scripts.mcp_server import create_mcp_server
   server = create_mcp_server()
   ```
2. 检查工具是否正确注册：
   ```python
   tools = await server.list_tools()
   print(len(tools))  # 应该是 3
   ```

### 问题：导入错误
**症状**:
```
ImportError: cannot import name 'get_available_financial_fields'
```

**说明**: 这是因为 MCP 工具是通过装饰器注册的，不是直接导出的函数。

**正确用法**:
```python
from scripts.mcp_server import create_mcp_server
server = create_mcp_server()
result = await server.call_tool('get_available_financial_fields', {...})
```

## 📊 数据问题

### 问题：Tushare API 调用失败
**症状**:
```
您的token不对，请确认
```

**解决方案**:
1. 登录 Tushare 平台检查 token 状态
2. 确认 API 积分是否充足
3. 检查是否有相应数据的访问权限

### 问题：数据格式不匹配
**症状**: 返回的数据字段与预期不符

**解决方案**:
1. 使用字段验证工具：
   ```python
   result = await server.call_tool('validate_financial_fields', {
       'statement_type': 'income',
       'fields': ['end_date', 'total_revenue']
   })
   ```
2. 查看可用字段列表：
   ```python
   result = await server.call_tool('get_available_financial_fields', {
       'statement_type': 'income'
   })
   ```

### 问题：重复数据或数据缺失
**症状**: 同一股票同一报告期有多条记录

**说明**: 这是正常的，系统会自动选择 `update_flag=1` 的记录。

**解决方案**: 检查 Service 层的 `update_flag` 过滤逻辑。

## 🧪 测试问题

### 问题：测试失败
**症状**: `pytest` 运行失败

**常见解决方案**:
1. 安装测试依赖：`uv sync --all-extras`
2. 检查测试环境变量：`TUSHARE_TOKEN=test_token`
3. 运行特定测试：`uv run pytest tests/test_mcp_server.py -v`

### 问题：Mock 测试不准确
**症状**: Mock 测试通过但真实 API 调用失败

**解决方案**:
1. 检查 Mock 对象是否正确配置
2. 验证真实 API 参数格式
3. 使用真实 API 进行集成测试

## 🔍 调试技巧

### 1. 启用调试日志
```bash
LOG_LEVEL=DEBUG uv run uvicorn tushare_query_mcp.main:app --reload
```

### 2. 检查 API 调用详情
```python
import logging
logging.basicConfig(level=logging.DEBUG)
# 这会显示详细的 HTTP 请求和响应信息
```

### 3. 验证配置
```python
from tushare_query_mcp.config import get_settings
settings = get_settings()
print(f"Token configured: {bool(settings.tushare_token)}")
print(f"Cache dir: {settings.cache_dir}")
```

### 4. 测试数据源连接
```python
from tushare_query_mcp.services.tushare_datasource import TushareDataSource
source = TushareDataSource("your_token")
health = await source.health_check()
print(health)
```

## 📈 性能问题

### 问题：响应速度慢
**可能原因**:
1. 缓存未命中
2. 网络延迟
3. API 调用频率限制

**优化方案**:
1. 增加缓存时间
2. 使用批量查询
3. 实现本地缓存预热

### 问题：内存使用过高
**解决方案**:
1. 定期清理过期缓存
2. 调整缓存大小限制
3. 使用磁盘缓存而非内存缓存

## 🌐 网络问题

### 问题：代理或防火墙限制
**症状**: 无法访问 Tushare API

**解决方案**:
1. 配置 HTTP 代理：
   ```bash
   export HTTP_PROXY=http://proxy.company.com:8080
   export HTTPS_PROXY=http://proxy.company.com:8080
   ```
2. 检查防火墙规则
3. 使用网络诊断工具

### 问题：DNS 解析问题
**症状**: 无法解析 Tushare API 域名

**解决方案**:
1. 更换 DNS 服务器
2. 使用 IP 地址直接访问
3. 检查 `/etc/hosts` 文件

## 🆘 获取帮助

### 查看详细错误信息
1. 检查应用日志
2. 启用 DEBUG 模式
3. 使用健康检查端点

### 社区资源
1. Tushare 官方文档：https://tushare.pro/document
2. FastAPI 文档：https://fastapi.tiangolo.com
3. Pydantic 文档：https://docs.pydantic.dev

### 报告问题
如果遇到无法解决的问题，请提供：
1. 完整的错误信息
2. 重现步骤
3. 相关配置信息
4. 系统环境信息