"""
arXiv Pulse 版本信息 - 动态从包元数据读取
"""

import importlib.metadata

# 从包元数据读取版本
try:
    __version__ = importlib.metadata.version("arxiv-pulse")
    # 解析版本信息元组
    try:
        __version_info__ = tuple(map(int, __version__.split(".")))
    except ValueError:
        # 如果版本号包含字母或其他字符，只取数字部分
        parts = []
        for part in __version__.split("."):
            # 提取数字部分
            digits = ""
            for char in part:
                if char.isdigit():
                    digits += char
                else:
                    break
            if digits:
                parts.append(int(digits))
            else:
                parts.append(0)
        __version_info__ = tuple(parts)

except importlib.metadata.PackageNotFoundError:
    # 包未安装时使用默认版本
    __version__ = "1.0.3"
    __version_info__ = (1, 0, 3)
