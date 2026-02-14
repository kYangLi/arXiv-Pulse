#!/usr/bin/env python3
"""
arXiv Pulse - Web 界面启动器
仅提供 serve 命令启动 Web 服务
"""

import atexit
import os
import signal
import socket
import subprocess
import sys
from pathlib import Path

import click

from arxiv_pulse.__version__ import __version__
from arxiv_pulse.lock import ServiceLock, check_and_acquire_lock


def _is_port_in_use(host: str, port: int) -> bool:
    """Check if a port is already in use"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex((host, port))
            return result == 0
    except Exception:
        return False


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version=__version__, prog_name="arXiv Pulse")
def cli():
    """arXiv Pulse - 智能 arXiv 文献追踪系统

    启动 Web 服务后，访问 http://localhost:8000 进行初始化配置和使用。
    """
    pass


# Global lock instance for cleanup
_lock_instance: ServiceLock | None = None


def _cleanup_lock():
    """Cleanup lock on exit"""
    global _lock_instance
    if _lock_instance:
        _lock_instance.release()
        _lock_instance = None


def _signal_handler(signum, frame):
    """Handle interrupt signals"""
    _cleanup_lock()
    click.echo("\n服务已停止")
    sys.exit(0)


@cli.command()
@click.argument("directory", type=click.Path(exists=False, file_okay=False), default=".")
@click.option("--host", default="127.0.0.1", help="服务监听地址")
@click.option("--port", default=8000, type=int, help="服务监听端口")
@click.option("--foreground", "-f", is_flag=True, help="前台运行模式（默认后台运行）")
@click.option("--force", is_flag=True, help="强制启动（忽略已有的锁）")
def serve(directory, host, port, foreground, force):
    """启动 Web 服务

    DIRECTORY: 数据存储目录（默认为当前目录）

    数据库位置: <DIRECTORY>/data/arxiv_papers.db

    示例:
        pulse serve                    # 后台运行（默认）
        pulse serve -f                 # 前台运行
        pulse serve --port 3000        # 使用 3000 端口
        pulse serve --force            # 强制启动（忽略已有实例）
    """
    global _lock_instance

    directory = Path(directory).resolve()
    data_dir = directory / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    db_path = data_dir / "arxiv_papers.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

    lock = ServiceLock(directory)
    is_locked, lock_info = lock.is_locked()

    if is_locked and not force:
        click.echo(f"\n{'=' * 50}")
        click.secho("  ⚠️  服务已在运行中", fg="yellow", bold=True)
        click.echo(f"{'=' * 50}\n")
        click.echo(lock.get_status_message(lock_info))
        click.echo(f"\n如需强制启动新实例，请使用 --force 参数")
        if lock_info:
            click.echo(f"或先停止当前服务: kill {lock_info.get('pid', '')}")
        sys.exit(1)

    if force and is_locked:
        click.secho("\n⚠️  警告: 强制模式，将覆盖已有锁文件", fg="yellow")
        lock.release()

    # Check if port is already in use
    if _is_port_in_use(host, port):
        click.echo(f"\n{'=' * 50}")
        click.secho(f"  ❌ 端口 {port} 已被占用", fg="red", bold=True)
        click.echo(f"{'=' * 50}\n")
        click.echo(f"请检查是否有其他服务正在使用端口 {port}")
        click.echo(f"或使用 --port 指定其他端口")
        if is_locked and lock_info:
            click.echo(f"\n如果这是 arXiv Pulse 的旧实例，请先停止: pulse stop")
        sys.exit(1)

    # Acquire lock
    acquired = lock.acquire(host, port)
    if not acquired:
        click.secho("❌ 无法获取服务锁", fg="red")
        sys.exit(1)

    _lock_instance = lock

    # Setup cleanup handlers
    atexit.register(_cleanup_lock)
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    click.echo(f"\n{'=' * 50}")
    click.echo("  arXiv Pulse - 智能文献追踪系统")
    click.echo(f"{'=' * 50}")
    click.echo(f"\n📂 数据目录: {directory}")
    click.echo(f"🌐 Web 界面: http://{host}:{port}")
    click.echo(f"📚 API 文档: http://{host}:{port}/docs")
    click.echo(f"🔄 运行模式: {'前台运行' if foreground else '后台运行'}")

    if foreground:
        import uvicorn

        click.echo("\n按 Ctrl+C 停止服务\n")
        try:
            uvicorn.run(
                "arxiv_pulse.web.app:app",
                host=host,
                port=port,
                log_level="info",
            )
        finally:
            _cleanup_lock()
    else:
        log_file = directory / "web.log"

        cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            "arxiv_pulse.web.app:app",
            "--host",
            host,
            "--port",
            str(port),
            "--log-level",
            "info",
        ]

        with open(log_file, "w") as log:
            process = subprocess.Popen(
                cmd,
                stdout=log,
                stderr=log,
                start_new_session=True,
                env={**os.environ, "DATABASE_URL": f"sqlite:///{directory}/data/arxiv_papers.db"},
            )

        # Update lock with actual PID
        lock.release()
        lock.acquire(host, port, pid=process.pid)
        _lock_instance = None  # Prevent atexit from cleaning up the lock

        click.echo(f"\n✅ 服务已在后台启动 (PID: {process.pid})")
        click.echo(f"📝 日志文件: {log_file}")
        click.echo(f"\n💡 停止服务: pulse stop")
        click.echo(f"   查看状态: pulse status")


@cli.command()
@click.argument("directory", type=click.Path(exists=False, file_okay=False), default=".")
def status(directory):
    """查看服务状态

    DIRECTORY: 数据存储目录（默认为当前目录）

    数据库位置: <DIRECTORY>/data/arxiv_papers.db
    """
    directory = Path(directory).resolve()
    lock = ServiceLock(directory)

    is_locked, info = lock.is_locked()

    click.echo(f"\n{'=' * 50}")
    click.echo("  arXiv Pulse - 服务状态")
    click.echo(f"{'=' * 50}\n")
    click.echo(f"📂 数据目录: {directory}")
    click.echo(f"🗄️  数据库: {directory}/data/arxiv_papers.db\n")

    if is_locked:
        click.secho("✅ 服务运行中", fg="green", bold=True)
        click.echo(lock.get_status_message(info))
    else:
        click.secho("⏹️  服务未运行", fg="yellow")


@cli.command()
@click.argument("directory", type=click.Path(exists=False, file_okay=False), default=".")
@click.option("--force", is_flag=True, help="强制停止（使用 SIGKILL）")
def stop(directory, force):
    """停止后台服务

    DIRECTORY: 数据存储目录（默认为当前目录）

    示例:
        pulse stop           # 停止当前目录的服务
        pulse stop --force   # 强制停止（如果普通停止无效）
    """
    import time

    directory = Path(directory).resolve()
    lock = ServiceLock(directory)

    is_locked, info = lock.is_locked()

    click.echo(f"\n{'=' * 50}")
    click.echo("  arXiv Pulse - 停止服务")
    click.echo(f"{'=' * 50}\n")
    click.echo(f"📂 数据目录: {directory}")

    if not is_locked:
        click.secho("\n⏹️  没有运行中的服务", fg="yellow")
        return

    if info:
        pid = info.get("pid")
        host = info.get("host", "unknown")
        port = info.get("port", "unknown")

        click.echo(f"🔍 发现运行中的服务: http://{host}:{port} (PID: {pid})")

        try:
            sig = signal.SIGKILL if force else signal.SIGTERM
            sig_name = "SIGKILL" if force else "SIGTERM"
            os.kill(pid, sig)
            click.echo(f"📤 已发送 {sig_name} 信号...")

            for _ in range(10):
                try:
                    os.kill(pid, 0)
                    time.sleep(0.5)
                except ProcessLookupError:
                    break

            try:
                os.kill(pid, 0)
                if not force:
                    click.secho("\n⚠️  进程未响应，尝试强制停止...", fg="yellow")
                    os.kill(pid, signal.SIGKILL)
                    time.sleep(1)
            except ProcessLookupError:
                pass

            lock.release()
            click.secho("\n✅ 服务已停止", fg="green", bold=True)
        except ProcessLookupError:
            lock.release()
            click.secho("\n✅ 进程已不存在，已清理锁文件", fg="green")
        except PermissionError:
            click.secho("\n❌ 没有权限停止该进程，请尝试使用 sudo", fg="red")
        except Exception as e:
            click.secho(f"\n❌ 停止失败: {e}", fg="red")
    else:
        lock.release()
        click.secho("\n✅ 已清理锁文件", fg="green")


if __name__ == "__main__":
    cli()
