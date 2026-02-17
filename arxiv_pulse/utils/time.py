"""
工具函数模块
"""

from datetime import UTC, datetime, timedelta


def get_workday_cutoff(days_back: int) -> datetime:
    """计算排除周末的截止日期"""
    current = datetime.now(UTC).replace(tzinfo=None)
    workdays_counted = 0
    days_to_go_back = 0

    while workdays_counted < days_back:
        days_to_go_back += 1
        if (current - timedelta(days=days_to_go_back)).weekday() < 5:
            workdays_counted += 1

    return current - timedelta(days=days_to_go_back)


def parse_time_range(time_range: str) -> int:
    """解析时间范围字符串，返回天数

    Args:
        time_range: 时间范围字符串，如 '1y'=1年、'6m'=6个月、'30d'=30天

    Returns:
        天数
    """
    if not time_range or time_range == "0":
        return 0

    time_range = time_range.lower()
    if time_range.endswith("d"):
        return int(time_range[:-1])
    elif time_range.endswith("m"):
        return int(time_range[:-1]) * 30
    elif time_range.endswith("y"):
        return int(time_range[:-1]) * 365
    else:
        return int(time_range)
