# -*- coding: utf-8 -*-
"""
tests/test_selftest.py —— 把各模块内置自检统一收进 pytest 入口
==============================================================

本仓原本只有脚本式的 `--selftest`（各自 print 结果 + 退出码），
本文件用 subprocess 逐条复跑 README / CI 里文档化的自检命令并断言退出码为 0，
使 13 个仓库具备统一的一键验证入口：

    python -m pytest tests -q

被测命令（与 .github/workflows/ci.yml 完全同源）：
  1. ai-prediction/fault_classifier.py --selftest   故障分级用例
  2. alerts/alert_engine.py --selftest              告警分级/抑制/工单
  3. ai-prediction/evaluate.py --selftest           RUL 置信区间 + 喂入口径回归锁

说明：这些自检在仓库内是"权威实现"，此处只做编排与退出码断言，
      不重复实现断言逻辑（避免两处口径漂移）。
"""

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

# 与 CI 同源的命令清单：(用例 id, 参数)
SELFTEST_COMMANDS = [
    ("fault_classifier", ["ai-prediction/fault_classifier.py", "--selftest"]),
    ("alert_engine", ["alerts/alert_engine.py", "--selftest"]),
    ("evaluate_rul_ci", ["ai-prediction/evaluate.py", "--selftest"]),
]


def _run(args):
    """在仓库根目录跑一条自检命令，返回 CompletedProcess。"""
    return subprocess.run(
        [sys.executable, *args],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
    )


@pytest.mark.parametrize("case_id,args", SELFTEST_COMMANDS, ids=[c[0] for c in SELFTEST_COMMANDS])
def test_selftest_exit_zero(case_id, args):
    proc = _run(args)
    assert proc.returncode == 0, (
        f"{case_id} 自检失败（exit={proc.returncode}）\n"
        f"--- stdout 尾部 ---\n{proc.stdout[-1500:]}\n"
        f"--- stderr 尾部 ---\n{proc.stderr[-800:]}"
    )
    # 自检必须真的跑出了内容（防止脚本被改成空跑）
    assert proc.stdout.strip(), f"{case_id} 无任何输出，疑似空跑"


def test_documented_commands_exist():
    """确保被测脚本都还在，避免命令清单与实际仓库脱节。"""
    missing = [args[0] for _, args in SELFTEST_COMMANDS if not (ROOT / args[0]).is_file()]
    assert not missing, f"以下自检脚本不存在：{missing}"
