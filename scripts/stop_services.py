#!/usr/bin/env python3
"""
停止所有 Tushare Query MCP 相关服务
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


def find_processes():
    """查找相关进程"""
    processes = []

    try:
        # 查找 uvicorn 进程
        result = subprocess.run(
            ["pgrep", "-f", "uvicorn.*tushare_query_mcp"],
            capture_output=True, text=True
        )
        if result.stdout.strip():
            for pid in result.stdout.strip().split('\n'):
                processes.append(('uvicorn', int(pid)))
    except FileNotFoundError:
        pass

    try:
        # 查找 start_server.py 进程
        result = subprocess.run(
            ["pgrep", "-f", "python.*start_server.py"],
            capture_output=True, text=True
        )
        if result.stdout.strip():
            for pid in result.stdout.strip().split('\n'):
                processes.append(('start_server', int(pid)))
    except FileNotFoundError:
        pass

    try:
        # 查找 start.py 进程
        result = subprocess.run(
            ["pgrep", "-f", "python.*start.py"],
            capture_output=True, text=True
        )
        if result.stdout.strip():
            for pid in result.stdout.strip().split('\n'):
                processes.append(('start', int(pid)))
    except FileNotFoundError:
        pass

    return processes


def stop_process(pid: int, name: str) -> bool:
    """停止单个进程"""
    try:
        # 首先尝试优雅终止
        os.kill(pid, signal.SIGTERM)

        # 等待进程结束
        for _ in range(5):
            try:
                os.kill(pid, 0)  # 检查进程是否存在
                time.sleep(1)
            except OSError:
                print_status(f"成功停止 {name} 进程 (PID: {pid})", "success")
                return True

        # 如果进程仍在运行，强制终止
        os.kill(pid, signal.SIGKILL)
        print_status(f"强制停止 {name} 进程 (PID: {pid})", "warning")
        return True

    except OSError as e:
        if e.errno == 3:  # No such process
            print_status(f"{name} 进程 (PID: {pid}) 已不存在", "info")
            return True
        else:
            print_status(f"停止 {name} 进程 (PID: {pid}) 失败: {e}", "error")
            return False


def stop_port_users():
    """停止占用8000端口的进程"""
    try:
        result = subprocess.run(
            ["lsof", "-ti", ":8000"],
            capture_output=True, text=True
        )
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            print_status(f"发现占用8000端口的进程: {', '.join(pids)}", "warning")

            for pid in pids:
                try:
                    os.kill(int(pid), signal.SIGTERM)
                    print_status(f"停止占用8000端口的进程 (PID: {pid})", "success")
                except (OSError, ValueError):
                    pass
    except (FileNotFoundError, subprocess.SubprocessError):
        pass


def main():
    """主函数"""
    print_status("Tushare Query MCP 服务停止器", "start")
    print("=" * 50)

    # 查找所有相关进程
    processes = find_processes()

    if not processes:
        print_status("没有发现运行中的相关服务", "info")
        print_status("检查端口占用情况...", "info")
        stop_port_users()
        print_status("所有服务已停止", "success")
        return

    print_status(f"发现 {len(processes)} 个相关进程:", "info")
    for name, pid in processes:
        print(f"  - {name}: PID {pid}")
    print("")

    # 停止所有进程
    stopped_count = 0
    for name, pid in processes:
        if stop_process(pid, name):
            stopped_count += 1

    # 额外检查端口占用
    stop_port_users()

    # 等待一下让进程完全结束
    time.sleep(2)

    # 最终检查
    remaining_processes = find_processes()
    if remaining_processes:
        print_status(f"警告: 仍有 {len(remaining_processes)} 个进程未停止", "warning")
        for name, pid in remaining_processes:
            print(f"  - {name}: PID {pid}")
    else:
        print_status(f"成功停止所有 {stopped_count} 个进程", "success")

    print_status("服务停止完成", "success")


if __name__ == "__main__":
    main()