# 配置变量参考

## 📋 环境变量配置

### 必需配置

#### `TUSHARE_TOKEN`
- **类型**: String
- **描述**: Tushare API 访问令牌
- **获取方式**: 在 https://tushare.pro 注册并获取
- **示例**: `your_tushare_token_here`
- **验证**: 不能为空且为有效格式

### 服务器配置

#### `API_HOST`
- **类型**: String
- **默认值**: `0.0.0.0`
- **描述**: API 服务器监听地址
- **常用值**:
  - `0.0.0.0` - 监听所有接口
  - `127.0.0.1` - 仅本地访问
  - `localhost` - 本地访问

#### `API_PORT`
- **类型**: Integer
- **默认值**: `8000`
- **范围**: 1-65535
- **描述**: API 服务器端口
- **注意**: 避免使用系统保留端口

### 缓存配置

#### `CACHE_DIR`
- **类型**: String
- **默认值**: `./.cache`
- **描述**: 缓存文件存储目录
- **自动创建**: 如果目录不存在会自动创建
- **权限**: 需要读写权限

#### `INCOME_CACHE_TTL`
- **类型**: Integer (秒)
- **默认值**: `604800` (7天)
- **描述**: 利润表数据缓存时间
- **建议**: 财务数据更新频率较低，可以设置较长缓存时间

#### `BALANCE_CACHE_TTL`
- **类型**: Integer (秒)
- **默认值**: `604800` (7天)
- **描述**: 资产负债表数据缓存时间

#### `CASHFLOW_CACHE_TTL`
- **类型**: Integer (秒)
- **默认值**: `604800` (7天)
- **描述**: 现金流量表数据缓存时间

#### `STOCK_CACHE_TTL`
- **类型**: Integer (秒)
- **默认值**: `2592000` (30天)
- **描述**: 股票基本信息缓存时间
- **说明**: 股票基本信息变化不频繁，可以设置更长缓存

### API 调用配置

#### `API_TIMEOUT`
- **类型**: Integer (秒)
- **默认值**: `30`
- **范围**: 1-300
- **描述**: Tushare API 调用超时时间
- **建议**: 网络条件较差时可以适当增加

#### `MAX_RETRIES`
- **类型**: Integer
- **默认值**: `3`
- **范围**: 0-10
- **描述**: API 调用失败时的最大重试次数
- **说明**: 用于处理临时网络问题

### 日志配置

#### `LOG_LEVEL`
- **类型**: String
- **默认值**: `INFO`
- **可选值**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- **描述**: 应用日志级别
- **建议**:
  - 开发环境: `DEBUG`
  - 生产环境: `INFO` 或 `WARNING`

## 📁 配置文件示例

### `.env.example`
```bash
# Tushare API Token (必需)
# 在 https://tushare.pro 注册并获取您的token
TUSHARE_TOKEN=your_tushare_token_here

# API服务器配置
API_HOST=0.0.0.0
API_PORT=8000

# 缓存配置
CACHE_DIR=./.cache
INCOME_CACHE_TTL=604800
BALANCE_CACHE_TTL=604800
CASHFLOW_CACHE_TTL=604800
STOCK_CACHE_TTL=2592000

# API调用配置
API_TIMEOUT=30
MAX_RETRIES=3

# 日志配置
LOG_LEVEL=INFO
```

### `.env` (生产环境)
```bash
# 生产环境配置示例
TUSHARE_TOKEN=your_production_token
API_HOST=0.0.0.0
API_PORT=8000
CACHE_DIR=/var/cache/tushare-query
INCOME_CACHE_TTL=86400
BALANCE_CACHE_TTL=86400
CASHFLOW_CACHE_TTL=86400
STOCK_CACHE_TTL=604800
API_TIMEOUT=60
MAX_RETRIES=5
LOG_LEVEL=WARNING
```

## 🔧 配置验证

### 自动验证
应用启动时会自动验证：
- `TUSHARE_TOKEN` 是否存在且不为空
- 端口号是否在有效范围内
- 日志级别是否为有效值
- 缓存目录是否可创建和写入

### 错误处理
- 缺少必需配置会导致应用启动失败
- 无效配置会使用默认值并记录警告
- 配置错误会在健康检查中显示

## 🚀 启动命令示例

### 开发环境
```bash
# 使用默认配置
uv run uvicorn tushare_query_mcp.main:app --reload

# 指定端口
uv run uvicorn tushare_query_mcp.main:app --port 8080 --reload

# 调试模式
LOG_LEVEL=DEBUG uv run uvicorn tushare_query_mcp.main:app --reload
```

### 生产环境
```bash
# 使用环境变量文件
export $(cat .env | xargs)
uv run uvicorn tushare_query_mcp.main:app --host 0.0.0.0 --port 8000

# 或直接传递环境变量
TUSHARE_TOKEN=your_token LOG_LEVEL=WARNING uv run uvicorn tushare_query_mcp.main:app
```

## 📊 配置监控

### 健康检查
访问 `/health` 端点查看当前配置状态：
```json
{
  "config": {
    "tushare_token_configured": true,
    "cache_directory": "./.cache",
    "log_level": "INFO"
  }
}
```

### 运行时配置
- 应用启动后无法动态修改配置
- 需要重启应用以应用新的配置
- 缓存目录变更可能需要手动迁移数据

## 🔒 安全注意事项

### 敏感信息保护
- `TUSHARE_TOKEN` 应保密存储
- 不要在代码中硬编码 token
- 使用环境变量或安全的密钥管理系统
- `.env` 文件应添加到 `.gitignore`

### 生产环境建议
- 使用强密码/随机 token
- 定期轮换 API token
- 监控 API 调用频率和配额使用情况
- 设置适当的缓存策略以减少 API 调用

## 🔍 故障排除

### 常见配置问题

1. **Token 无效**
   - 检查 token 是否正确
   - 确认 token 在 Tushare 平台是否有效
   - 查看是否有权限访问相应数据

2. **端口被占用**
   - 更改 `API_PORT` 到其他可用端口
   - 检查是否有其他服务占用相同端口

3. **缓存目录权限**
   - 确保应用有权限创建和写入缓存目录
   - 检查磁盘空间是否充足

4. **API 超时**
   - 增加 `API_TIMEOUT` 值
   - 检查网络连接状态
   - 考虑使用代理或 CDN