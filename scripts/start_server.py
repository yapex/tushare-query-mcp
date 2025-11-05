#!/usr/bin/env python3
"""
Tushare Query MCP 服务启动器 (简化版)
专为 Poe 任务管理设计
"""

import subprocess
import sys
import time
import signal
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 服务进程管理
processes = {}


def print_status(msg: str, status: str = "info"):
    """打印状态信息"""
    symbols = {
        "info": "ℹ️",
        "success": "✅",
        "error": "❌",
        "warning": "⚠️",
        "start": "🚀"
    }
    symbol = symbols.get(status, "ℹ️")
    print(f"{symbol} {msg}")


def check_requirements():
    """检查项目依赖和环境"""
    print_status("检查环境...")

    # 检查 TUSHARE_TOKEN
    token = os.getenv("TUSHARE_TOKEN")
    if not token:
        print_status("TUSHARE_TOKEN 环境变量未设置", "error")
        print_status("请设置 TUSHARE_TOKEN 或创建 .env 文件", "warning")
        return False

    print_status("TUSHARE_TOKEN 已配置", "success")

    # 检查依赖
    try:
        import uvicorn
        from tushare_query_mcp.main import app
        from scripts.mcp_server import create_mcp_server
        print_status("项目依赖检查通过", "success")
    except ImportError as e:
        print_status(f"依赖检查失败: {e}", "error")
        print_status("请运行: uv sync", "warning")
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

    print_status(f"启动 FastAPI 服务器: http://{host}:{port}", "start")
    print_status(f"执行命令: {' '.join(cmd)}", "info")

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1
        )

        # 等待一小段时间检查启动状态
        time.sleep(2)

        if process.poll() is not None:
            # 进程已经退出，获取错误信息
            stdout, stderr = process.communicate()
            print_status(f"FastAPI 进程退出，返回码: {process.returncode}", "error")
            if stderr:
                print_status(f"错误输出: {stderr}", "error")
            if stdout:
                print_status(f"标准输出: {stdout}", "warning")
            return None

        return process
    except Exception as e:
        print_status(f"FastAPI 启动失败: {e}", "error")
        return None


def show_services_info():
    """显示服务信息"""
    print_status("服务启动完成！")
    print("")
    print("📚 访问地址:")
    print("  📖 Swagger 文档: http://localhost:8000/docs")
    print("  🔍 ReDoc 文档: http://localhost:8000/redoc")
    print("  💚 健康检查: http://localhost:8000/health")
    print("")
    print("🤖 MCP 服务器:")
    print("  - 通过 Python 代码调用 MCP 工具")
    print("  - 可用工具: query_stock_financials, get_available_financial_fields, validate_financial_fields")
    print("")
    print("⏰ 服务监控中... (按 Ctrl+C 停止)")


def signal_handler(signum, frame):
    """处理中断信号"""
    print_status("正在停止服务...", "warning")
    stop_services()
    sys.exit(0)


def stop_services():
    """停止所有服务"""
    for name, process in processes.items():
        if process and process.poll() is None:
            print_status(f"停止 {name} 服务...", "warning")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
    processes.clear()


def monitor_services():
    """监控服务状态"""
    try:
        # 持续监控
        while True:
            time.sleep(1)

            # 检查 FastAPI 进程状态
            if "fastapi" in processes:
                process = processes["fastapi"]
                if process.poll() is not None:
                    print_status("FastAPI 服务意外停止", "error")
                    break

    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)


def main():
    """主启动函数"""
    print_status("Tushare Query MCP 服务启动器", "start")
    print("=" * 50)

    # 环境检查
    if not check_requirements():
        sys.exit(1)

    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # 启动 FastAPI 服务
        fastapi_process = start_fastapi()
        if fastapi_process:
            processes["fastapi"] = fastapi_process

            # 等待服务启动
            time.sleep(3)

            # 验证 FastAPI 启动
            if fastapi_process.poll() is None:
                print_status("FastAPI 服务启动成功", "success")

                # 验证 MCP 服务器创建
                try:
                    from scripts.mcp_server import create_mcp_server
                    server = create_mcp_server()
                    import asyncio
                    tools = asyncio.run(server.list_tools())
                    print_status(f"MCP 服务器创建成功 ({len(tools)} 个工具)", "success")
                except Exception as e:
                    print_status(f"MCP 服务器警告: {e}", "warning")

                # 显示服务信息
                show_services_info()

                # 开始监控
                monitor_services()
            else:
                print_status("FastAPI 服务启动失败", "error")
                sys.exit(1)
        else:
            print_status("无法启动 FastAPI 服务", "error")
            sys.exit(1)

    except Exception as e:
        print_status(f"启动失败: {e}", "error")
        stop_services()
        sys.exit(1)


if __name__ == "__main__":
    main()