#!/usr/bin/env python3
"""
统一输出管理器 - 提供优雅的控制台输出体验

提供以下标签级别的输出：
[do]      - 正在执行的操作
[done]    - 操作完成
[tips]    - 提示信息
[info]    - 一般信息
[warn]    - 警告信息
[error]   - 错误信息（简洁）
[debug]   - 调试信息（默认不显示）

所有详细日志同时写入日志文件，控制台只显示简洁信息。
"""

import sys
import os
import time
from typing import Optional, Dict, Any
import logging
from enum import Enum


class OutputLevel(Enum):
    """输出级别"""

    DO = "do"
    DONE = "done"
    TIPS = "tips"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"
    DEBUG = "debug"


class OutputManager:
    """统一输出管理器"""

    # 颜色定义
    COLORS = {
        "do": "\033[94m",  # 蓝色
        "done": "\033[92m",  # 绿色
        "tips": "\033[96m",  # 青色
        "info": "\033[97m",  # 白色
        "warn": "\033[93m",  # 黄色
        "error": "\033[91m",  # 红色
        "debug": "\033[90m",  # 灰色
        "reset": "\033[0m",  # 重置
    }

    # 标签显示格式
    LABELS = {
        OutputLevel.DO: "[执行]",
        OutputLevel.DONE: "[完成]",
        OutputLevel.TIPS: "[提示]",
        OutputLevel.INFO: "[信息]",
        OutputLevel.WARN: "[警告]",
        OutputLevel.ERROR: "[错误]",
        OutputLevel.DEBUG: "[调试]",
    }

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._initialized = True
            self._console_enabled = True
            self._file_logger = None
            self._min_level = OutputLevel.DO  # 默认显示DO及以上（包括DONE, TIPS, INFO等）
            self._suppressed_modules = set()
            self._setup_file_logger()

            # 抑制第三方库的详细日志
            self._suppress_third_party_logs()

    def _setup_file_logger(self):
        """设置文件日志记录器"""
        # 创建日志目录
        os.makedirs("logs", exist_ok=True)

        # 配置文件日志记录器
        self._file_logger = logging.getLogger("arxiv_crawler")
        self._file_logger.setLevel(logging.DEBUG)

        # 移除现有处理器
        for handler in self._file_logger.handlers[:]:
            self._file_logger.removeHandler(handler)

        # 添加文件处理器
        file_handler = logging.FileHandler("logs/arxiv_pulse.log", encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)
        self._file_logger.addHandler(file_handler)

    def _suppress_third_party_logs(self):
        """抑制第三方库的详细日志"""
        # 设置第三方库的日志级别为WARNING或更高
        suppressed_modules = ["arxiv", "httpx", "httpcore", "urllib3", "asyncio"]

        for module in suppressed_modules:
            logger = logging.getLogger(module)
            logger.setLevel(logging.WARNING)
            # 禁用传播，避免被根日志记录器处理
            logger.propagate = False

    def _should_output(self, level: OutputLevel, module: Optional[str] = None) -> bool:
        """检查是否应该输出"""
        if module and module in self._suppressed_modules:
            return False

        # 检查级别
        level_order = {
            OutputLevel.DO: 0,
            OutputLevel.DONE: 1,
            OutputLevel.TIPS: 2,
            OutputLevel.INFO: 3,
            OutputLevel.WARN: 4,
            OutputLevel.ERROR: 5,
            OutputLevel.DEBUG: 6,
        }

        return level_order[level] >= level_order[self._min_level]

    def _output(
        self,
        level: OutputLevel,
        message: str,
        module: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """统一输出方法"""
        # 记录到文件日志
        log_level = {
            OutputLevel.DO: logging.INFO,
            OutputLevel.DONE: logging.INFO,
            OutputLevel.TIPS: logging.INFO,
            OutputLevel.INFO: logging.INFO,
            OutputLevel.WARN: logging.WARNING,
            OutputLevel.ERROR: logging.ERROR,
            OutputLevel.DEBUG: logging.DEBUG,
        }[level]

        # 构建详细日志消息
        log_message = message
        if module:
            log_message = f"[{module}] {message}"
        if details:
            details_str = " ".join(f"{k}={v}" for k, v in details.items())
            log_message = f"{log_message} | {details_str}"

        # 写入文件日志
        self._file_logger.log(log_level, log_message)

        # 控制台输出
        if self._console_enabled and self._should_output(level, module):
            # 获取标签和颜色
            label = self.LABELS[level]
            color = self.COLORS[level.value]
            reset = self.COLORS["reset"]

            # 构建输出行
            output = f"{color}{label}{reset} {message}"

            # 输出到控制台
            print(output, file=sys.stderr if level == OutputLevel.ERROR else sys.stdout)
            sys.stdout.flush()

    # 公共方法
    @classmethod
    def do(cls, message: str, module: Optional[str] = None, **details):
        """正在执行的操作"""
        cls()._output(OutputLevel.DO, message, module, details)

    @classmethod
    def done(cls, message: str, module: Optional[str] = None, **details):
        """操作完成"""
        cls()._output(OutputLevel.DONE, message, module, details)

    @classmethod
    def tips(cls, message: str, module: Optional[str] = None, **details):
        """提示信息"""
        cls()._output(OutputLevel.TIPS, message, module, details)

    @classmethod
    def info(cls, message: str, module: Optional[str] = None, **details):
        """一般信息"""
        cls()._output(OutputLevel.INFO, message, module, details)

    @classmethod
    def warn(cls, message: str, module: Optional[str] = None, **details):
        """警告信息"""
        cls()._output(OutputLevel.WARN, message, module, details)

    @classmethod
    def error(cls, message: str, module: Optional[str] = None, **details):
        """错误信息（简洁）"""
        cls()._output(OutputLevel.ERROR, message, module, details)

    @classmethod
    def debug(cls, message: str, module: Optional[str] = None, **details):
        """调试信息"""
        cls()._output(OutputLevel.DEBUG, message, module, details)

    # 配置方法
    @classmethod
    def set_min_level(cls, level: OutputLevel):
        """设置最小输出级别"""
        cls()._min_level = level

    @classmethod
    def suppress_module(cls, module: str):
        """抑制指定模块的输出"""
        cls()._suppressed_modules.add(module)

    @classmethod
    def enable_console(cls, enabled: bool = True):
        """启用/禁用控制台输出"""
        cls()._console_enabled = enabled

    @classmethod
    def get_file_logger(cls) -> logging.Logger:
        """获取文件日志记录器"""
        return cls()._file_logger


# 简化别名
output = OutputManager
