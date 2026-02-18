"""
ArXiv-Pulse 系统测试运行器

顺序执行所有测试，打印结果汇总
"""

import subprocess
import sys
from pathlib import Path


TEST_FILES = [
    "test_01_init.py",
    "test_02_navigation.py",
    "test_03_home.py",
    "test_04_recent.py",
    "test_05_collections.py",
    "test_06_chat.py",
    "test_07_settings.py",
    "test_08_export.py",
]


def run_test(test_file: str) -> tuple[bool, str]:
    """运行单个测试文件，返回 (是否通过, 输出)"""
    print(f"\n{'=' * 60}")
    print(f"  Running: {test_file}")
    print("=" * 60)

    result = subprocess.run(
        [sys.executable, "-m", "pytest", test_file, "-v", "-s", "--tb=short"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent,
    )

    output = result.stdout + result.stderr
    passed = result.returncode == 0

    return passed, output


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("  ArXiv-Pulse 系统测试套件")
    print("=" * 60)

    results = {}

    for test_file in TEST_FILES:
        passed, output = run_test(test_file)
        results[test_file] = passed

        if passed:
            print(f"\n✅ {test_file} PASSED")
        else:
            print(f"\n❌ {test_file} FAILED")
            print("\n输出详情:")
            print(output[-2000:] if len(output) > 2000 else output)

    print("\n" + "=" * 60)
    print("  测试结果汇总")
    print("=" * 60)

    passed_count = sum(1 for p in results.values() if p)
    total_count = len(results)

    for test_file, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {test_file}")

    print("\n" + "-" * 60)
    print(f"  通过: {passed_count}/{total_count}")
    print("-" * 60)

    if passed_count == total_count:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n⚠️  {total_count - passed_count} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
