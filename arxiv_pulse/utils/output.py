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

所有输出仅显示在控制台，不写入日志文件。
"""

import logging
import os
import sys
from enum import Enum
from typing import Any


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

    COLORS = {
        "do": "\033[94m",
        "done": "\033[92m",
        "tips": "\033[96m",
        "info": "\033[97m",
        "warn": "\033[93m",
        "error": "\033[91m",
        "debug": "\033[90m",
        "reset": "\033[0m",
    }

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
            log_level = os.getenv("LOG_LEVEL", "INFO").upper()
            level_map = {
                "DEBUG": OutputLevel.DEBUG,
                "INFO": OutputLevel.INFO,
                "WARNING": OutputLevel.WARN,
                "WARN": OutputLevel.WARN,
                "ERROR": OutputLevel.ERROR,
                "DO": OutputLevel.DO,
                "DONE": OutputLevel.DONE,
                "TIPS": OutputLevel.TIPS,
            }
            self._min_level = level_map.get(log_level, OutputLevel.INFO)
            self._suppressed_modules = set()
            self._file_logger = logging.getLogger("arxiv_pulse")
            self._file_logger.setLevel(logging.DEBUG)
            if not self._file_logger.handlers:
                self._file_logger.addHandler(logging.NullHandler())

            self._suppress_third_party_logs()

    def _suppress_third_party_logs(self):
        """抑制第三方库的详细日志"""
        suppressed_modules = ["arxiv", "httpx", "httpcore", "urllib3", "asyncio"]

        for module in suppressed_modules:
            logger = logging.getLogger(module)
            logger.setLevel(logging.WARNING)
            logger.propagate = False

    def _should_output(self, level: OutputLevel, module: str | None = None) -> bool:
        """检查是否应该输出"""
        if module and module in self._suppressed_modules:
            return False

        level_order = {
            OutputLevel.DEBUG: 0,
            OutputLevel.INFO: 1,
            OutputLevel.WARN: 2,
            OutputLevel.ERROR: 3,
            OutputLevel.DO: 4,
            OutputLevel.DONE: 5,
            OutputLevel.TIPS: 6,
        }

        return level_order[level] >= level_order[self._min_level]

    def _output(
        self,
        level: OutputLevel,
        message: str,
        module: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        """统一输出方法"""
        if self._console_enabled and self._should_output(level, module):
            label = self.LABELS[level]
            color = self.COLORS[level.value]
            reset = self.COLORS["reset"]

            output = f"{color}{label}{reset} {message}"

            print(output, file=sys.stderr if level == OutputLevel.ERROR else sys.stdout)
            sys.stdout.flush()

    @classmethod
    def do(cls, message: str, module: str | None = None, **details):
        """正在执行的操作"""
        cls()._output(OutputLevel.DO, message, module, details)

    @classmethod
    def done(cls, message: str, module: str | None = None, **details):
        """操作完成"""
        cls()._output(OutputLevel.DONE, message, module, details)

    @classmethod
    def tips(cls, message: str, module: str | None = None, **details):
        """提示信息"""
        cls()._output(OutputLevel.TIPS, message, module, details)

    @classmethod
    def info(cls, message: str, module: str | None = None, **details):
        """一般信息"""
        cls()._output(OutputLevel.INFO, message, module, details)

    @classmethod
    def warn(cls, message: str, module: str | None = None, **details):
        """警告信息"""
        cls()._output(OutputLevel.WARN, message, module, details)

    @classmethod
    def error(cls, message: str, module: str | None = None, **details):
        """错误信息（简洁）"""
        cls()._output(OutputLevel.ERROR, message, module, details)

    @classmethod
    def debug(cls, message: str, module: str | None = None, **details):
        """调试信息"""
        cls()._output(OutputLevel.DEBUG, message, module, details)

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
        instance = cls()
        if instance._file_logger is None:
            instance._file_logger = logging.getLogger("arxiv_pulse_fallback")
            instance._file_logger.setLevel(logging.DEBUG)
            if not instance._file_logger.handlers:
                instance._file_logger.addHandler(logging.NullHandler())
        assert instance._file_logger is not None
        return instance._file_logger


output = OutputManager
