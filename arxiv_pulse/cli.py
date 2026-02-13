#!/usr/bin/env python3
"""
arXiv Pulse - Web 界面启动器
仅提供 serve 命令启动 Web 服务
"""

import subprocess
import sys
from pathlib import Path

import click

from arxiv_pulse.__version__ import __version__


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version=__version__, prog_name="arXiv Pulse")
def cli():
    """arXiv Pulse - 智能 arXiv 文献追踪系统

    启动 Web 服务后，访问 http://localhost:8000 进行初始化配置和使用。
    """
    pass


@cli.command()
@click.argument("directory", type=click.Path(exists=False, file_okay=False), default=".")
@click.option("--host", default="127.0.0.1", help="服务监听地址")
@click.option("--port", default=8000, help="服务监听端口")
@click.option("--detach", is_flag=True, help="后台运行模式")
def serve(directory, host, port, detach):
    """启动 Web 服务

    DIRECTORY: 数据存储目录（默认为当前目录）

    示例:
        pulse serve                    # 在当前目录启动服务
        pulse serve /path/to/data      # 在指定目录启动服务
        pulse serve --port 3000        # 使用 3000 端口
        pulse serve --detach           # 后台运行
    """
    directory = Path(directory).resolve()

    (directory / "data").mkdir(parents=True, exist_ok=True)

    env_file = directory / ".env"
    if not env_file.exists():
        env_file.write_text(f"DATABASE_URL=sqlite:///{directory}/data/arxiv_papers.db\n")

    os.environ["DATABASE_URL"] = f"sqlite:///{directory}/data/arxiv_papers.db"

    click.echo(f"\n{'=' * 50}")
    click.echo("  arXiv Pulse - 智能文献追踪系统")
    click.echo(f"{'=' * 50}")
    click.echo(f"\n📂 数据目录: {directory}")
    click.echo(f"🌐 Web 界面: http://{host}:{port}")
    click.echo(f"📚 API 文档: http://{host}:{port}/docs")
    click.echo(f"🔄 运行模式: {'后台运行' if detach else '前台运行'}")

    if detach:
        log_file = directory / "data" / "web.log"
        log_file.parent.mkdir(exist_ok=True)

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

        click.echo(f"\n✅ 服务已在后台启动 (PID: {process.pid})")
        click.echo(f"📝 日志文件: {log_file}")
        click.echo(f"\n停止服务: kill {process.pid}")
    else:
        import uvicorn

        click.echo("\n按 Ctrl+C 停止服务\n")
        uvicorn.run(
            "arxiv_pulse.web.app:app",
            host=host,
            port=port,
            log_level="info",
        )


import os

if __name__ == "__main__":
    cli()
