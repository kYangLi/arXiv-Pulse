"""
ArXiv-Pulse Test Configuration

pytest 配置、fixtures 和通用工具函数
"""

import os
import signal
import sqlite3
import subprocess
import time
from pathlib import Path

import pytest
from playwright.sync_api import Page, sync_playwright

# 配置
BASE_URL = os.getenv("BASE_URL", "http://192.168.219.3:33033")
INIT_PORT = int(os.getenv("INIT_PORT", "33034"))
TEST_DB_PATH = Path(__file__).parent / "data" / "arxiv_papers.db"
INIT_DATA_DIR = Path(__file__).parent / "init_data"
PROJECT_ROOT = Path(__file__).parent.parent


def read_db_config() -> dict:
    """从测试数据库读取 AI API 配置"""
    if not TEST_DB_PATH.exists():
        return {}

    conn = sqlite3.connect(TEST_DB_PATH)
    cursor = conn.cursor()

    config = {}
    for key in ["ai_api_key", "ai_model", "ai_base_url", "translate_language"]:
        try:
            cursor.execute("SELECT value FROM system_config WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row and row[0]:
                config[key] = row[0]
        except sqlite3.OperationalError:
            pass

    conn.close()
    return config


def start_init_server(port: int, data_dir: Path) -> subprocess.Popen:
    """启动临时服务实例用于 init 测试"""
    data_dir.mkdir(parents=True, exist_ok=True)

    proc = subprocess.Popen(
        [
            "pulse",
            "serve",
            str(data_dir),
            "--port",
            str(port),
            "--host",
            "0.0.0.0",
            "--allow-non-localhost-access-with-plaintext-transmission-risk",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(PROJECT_ROOT),
        preexec_fn=os.setsid,
    )

    time.sleep(3)

    if proc.poll() is not None:
        raise RuntimeError(f"Server failed to start: {proc.stderr.read().decode()}")

    return proc


def stop_init_server(proc: subprocess.Popen):
    """停止临时服务实例"""
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        proc.wait(timeout=5)
    except Exception:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except Exception:
            pass


def expand_bottom_nav(page: Page):
    """展开底部导航栏"""
    bottom_nav = page.locator(".bottom-nav")
    if bottom_nav.is_visible():
        bottom_nav.hover()
        page.wait_for_timeout(300)


def navigate_to(page: Page, target: str):
    """导航到指定页面"""
    expand_bottom_nav(page)

    nav_map = {
        "home": "首页",
        "recent": "近期论文",
        "sync": "数据管理",
        "collections": "论文集",
    }

    target_text = nav_map.get(target, target)
    btn = page.locator(f"text={target_text}")

    for _ in range(3):
        expand_bottom_nav(page)
        if btn.count() > 0:
            btn.first.click()
            page.wait_for_timeout(500)
            return

    page.locator(f".nav-item:has-text('{target_text}')").first.click()
    page.wait_for_timeout(500)


def get_console_errors(page: Page) -> list:
    """获取控制台错误列表"""
    errors = []

    def handler(msg):
        if msg.type == "error":
            errors.append(f"[console error] {msg.text}")

    page.on("console", handler)
    page.on("pageerror", lambda err: errors.append(f"[page error] {err}"))

    return errors


@pytest.fixture
def api_config() -> dict:
    """AI API 配置 fixture"""
    return read_db_config()


@pytest.fixture
def browser_page():
    """创建浏览器页面，自动捕获错误"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        page.set_default_timeout(60000)
        page.set_default_navigation_timeout(60000)

        errors = get_console_errors(page)
        page._test_errors = errors

        yield page

        browser.close()


@pytest.fixture
def init_server():
    """启动临时服务用于 init 测试"""
    port = INIT_PORT
    data_dir = INIT_DATA_DIR

    proc = start_init_server(port, data_dir)

    yield {
        "url": f"http://192.168.219.3:{port}",
        "port": port,
        "data_dir": data_dir,
        "proc": proc,
    }

    stop_init_server(proc)


@pytest.fixture
def clean_browser_page():
    """创建干净浏览器页面（无缓存）用于 init 测试"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        page.set_default_timeout(60000)
        page.set_default_navigation_timeout(60000)

        errors = get_console_errors(page)
        page._test_errors = errors

        yield page

        browser.close()
