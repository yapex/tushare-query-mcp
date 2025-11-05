#!/usr/bin/env python3
"""
Tushare Query MCP 服务启动器
一键启动 FastAPI 和 MCP 服务器
"""

import asyncio
import subprocess
import sys
import time
import signal
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    import typer
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.live import Live
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    typer = None


app = typer.Typer(help="Tushare Query MCP 服务管理器") if typer else None
console = Console() if RICH_AVAILABLE else None

# 服务进程管理
processes = {}


def print_simple(msg: str, style: str = None):
    """简单打印（当 rich 不可用时）"""
    if console:
        console.print(msg, style=style)
    else:
        print(msg)


def check_requirements():
    """检查项目依赖和环境"""
    if not console:
        print("🔍 检查环境...")

    # 检查 TUSHARE_TOKEN
    token = os.getenv("TUSHARE_TOKEN")
    if not token:
        print_simple("❌ TUSHARE_TOKEN 环境变量未设置", "red")
        print_simple("💡 请设置 TUSHARE_TOKEN 或创建 .env 文件", "yellow")
        return False

    if console:
        print("✅ TUSHARE_TOKEN 已配置", "green")
    else:
        print("✅ TUSHARE_TOKEN 已配置")

    # 检查依赖
    try:
        import uvicorn
        from tushare_query_mcp.main import app
        from scripts.mcp_server import create_mcp_server
        if console:
            print("✅ 项目依赖检查通过", "green")
        else:
            print("✅ 项目依赖检查通过")
    except ImportError as e:
        print_simple(f"❌ 依赖检查失败: {e}", "red")
        print_simple("💡 请运行: uv sync", "yellow")
        return False

    return True


def start_fastapi(port: int = 8000, host: str = "0.0.0.0", reload: bool = True):
    """启动 FastAPI 服务器"""
    cmd = [
        "uv", "run", "uvicorn",
        "tushare_query_mcp.main:app",
        "--host", host,
        "--port", str(port)
    ]

    if reload:
        cmd.append("--reload")

    if console:
        console.print(f"🚀 启动 FastAPI 服务器: http://{host}:{port}", "blue")

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        return process
    except Exception as e:
        print_simple(f"❌ FastAPI 启动失败: {e}", "red")
        return None


def print_mcp_info():
    """打印 MCP 服务器信息"""
    info_text = """
MCP 服务器已创建，可通过以下方式使用：

1. Python 代码:
```python
from scripts.mcp_server import create_mcp_server

# 创建服务器
server = create_mcp_server()

# 调用工具
result = await server.call_tool('query_stock_financials', {
    'ts_code': '600519.SH',
    'statement_type': 'income',
    'fields': ['end_date', 'total_revenue']
})
```

2. Claude Code 集成:
   - 在 Claude Code 中配置 MCP 服务器
   - 使用工具查询财务数据

可用工具:
- query_stock_financials: 查询股票财务数据
- get_available_financial_fields: 获取可用字段
- validate_financial_fields: 验证字段有效性
"""

    if console:
        console.print(Panel(info_text, title="🤖 MCP 服务器信息", border_style="green"))
    else:
        print("🤖 MCP 服务器信息:")
        print(info_text)


def show_status():
    """显示服务状态"""
    if not console:
        print("📊 服务状态:")
        return

    table = Table(title="🎯 Tushare Query MCP 服务状态")
    table.add_column("服务", style="cyan", no_wrap=True)
    table.add_column("状态", style="green")
    table.add_column("访问地址", style="blue")
    table.add_column("说明", style="white")

    # FastAPI 状态
    fastapi_running = "fastapi" in processes and processes["fastapi"].poll() is None
    fastapi_status = "✅ 运行中" if fastapi_running else "❌ 未运行"
    fastapi_url = "http://localhost:8000" if fastapi_running else "-"
    fastapi_desc = "REST API + Swagger文档"

    table.add_row("FastAPI", fastapi_status, fastapi_url, fastapi_desc)
    table.add_row("MCP", "✅ 就绪", "-", "通过代码调用工具")

    console.print(table)


def signal_handler(signum, frame):
    """处理中断信号"""
    print_simple("\n🛑 正在停止服务...", "yellow")
    stop_services()
    sys.exit(0)


def stop_services():
    """停止所有服务"""
    for name, process in processes.items():
        if process and process.poll() is None:
            print_simple(f"🛑 停止 {name} 服务...", "yellow")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
    processes.clear()


def monitor_services():
    """监控服务状态"""
    if console:
        console.print("🎯 服务启动完成！按 Ctrl+C 停止所有服务", "green")
        print_simple("\n📚 访问地址:", "blue")
        print_simple("  📖 Swagger 文档: http://localhost:8000/docs", "blue")
        print_simple("  🔍 ReDoc 文档: http://localhost:8000/redoc", "blue")
        print_simple("  💚 健康检查: http://localhost:8000/health", "blue")
        print_simple("  🤖 MCP 服务器: 通过代码调用", "blue")

        print_mcp_info()

        # 显示状态表格
        show_status()

        print_simple("\n⏰ 服务监控中... (按 Ctrl+C 停止)", "yellow")

    try:
        # 持续监控
        while True:
            time.sleep(1)

            # 检查 FastAPI 进程状态
            if "fastapi" in processes:
                process = processes["fastapi"]
                if process.poll() is not None:
                    print_simple("❌ FastAPI 服务意外停止", "red")
                    break

    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)


if typer:

    @app.command()
    def start(
        port: int = typer.Option(8000, "--port", "-p", help="FastAPI 服务器端口"),
        host: str = typer.Option("0.0.0.0", "--host", "-h", help="FastAPI 服务器地址"),
        reload: bool = typer.Option(True, "--reload/--no-reload", help="是否启用热重载"),
        check: bool = typer.Option(True, "--check/--no-check", help="是否检查环境")
    ):
        """启动所有服务"""
        print_simple("🎯 Tushare Query MCP 服务启动器", "cyan")
        print_simple("=" * 50, "cyan")

        # 环境检查
        if check and not check_requirements():
            sys.exit(1)

        # 注册信号处理
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            # 启动 FastAPI 服务
            fastapi_process = start_fastapi(port=port, host=host, reload=reload)
            if fastapi_process:
                processes["fastapi"] = fastapi_process

                # 等待服务启动
                time.sleep(2)

                # 验证 FastAPI 启动
                if fastapi_process.poll() is None:
                    print_simple("✅ FastAPI 服务启动成功", "green")

                    # 验证 MCP 服务器创建
                    try:
                        from scripts.mcp_server import create_mcp_server
                        server = create_mcp_server()
                        tools = asyncio.run(server.list_tools())
                        print_simple(f"✅ MCP 服务器创建成功 ({len(tools)} 个工具)", "green")
                    except Exception as e:
                        print_simple(f"⚠️ MCP 服务器警告: {e}", "yellow")

                    # 开始监控
                    monitor_services()
                else:
                    print_simple("❌ FastAPI 服务启动失败", "red")
                    sys.exit(1)
            else:
                print_simple("❌ 无法启动 FastAPI 服务", "red")
                sys.exit(1)

        except Exception as e:
            print_simple(f"❌ 启动失败: {e}", "red")
            stop_services()
            sys.exit(1)

    @app.command()
    def status():
        """查看服务状态"""
        show_status()

    @app.command()
    def stop():
        """停止所有服务"""
        print_simple("🛑 停止所有服务...", "yellow")
        stop_services()
        print_simple("✅ 所有服务已停止", "green")

else:
    console = None


def simple_start():
    """简单启动模式"""
    print("🎯 Tushare Query MCP 服务启动器")
    print("=" * 50)

    if not check_requirements():
        sys.exit(1)

    try:
        fastapi_process = start_fastapi()
        if fastapi_process:
            processes["fastapi"] = fastapi_process
            time.sleep(2)

            if fastapi_process.poll() is None:
                print("✅ FastAPI 服务启动成功")
                print("📚 访问地址:")
                print("  📖 Swagger 文档: http://localhost:8000/docs")
                print("  🔍 ReDoc 文档: http://localhost:8000/redoc")
                print("  💚 健康检查: http://localhost:8000/health")

                monitor_services()
            else:
                print("❌ FastAPI 服务启动失败")
                sys.exit(1)
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        stop_services()
        sys.exit(1)


if __name__ == "__main__":
    if typer:
        # 如果有参数，使用 typer 解析
        if len(sys.argv) > 1:
            app()
        else:
            # 没有参数时，默认启动服务
            simple_start()
    else:
        # 简单模式：直接启动
        simple_start()