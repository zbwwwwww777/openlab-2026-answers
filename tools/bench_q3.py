#!/usr/bin/env python3
"""第 3 题：跑三档推理并把结果落成 UTF-8 证据文件。

之前速度数字只在终端里出现过一次、没存盘，而且 llama-cli 的 stdout 在
本机是 UTF-16，直接 cat 会看着像乱码。这里统一用 UTF-8 落盘。

用法：
    python tools/bench_q3.py
产出：
    res/q3_evidence/speed_compare.txt
"""

from __future__ import annotations

import re
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "res" / "q3_evidence" / "speed_compare.txt"

EXE = Path(r"C:\Users\lennovo\dev\llm\llama.cpp\build\bin\llama-cli.exe")
MODEL = Path(r"C:\Users\lennovo\Downloads\gemma-4-E2B-it-Q4_0.gguf")
PROMPT = "用一句话解释什么是版本控制系统 Git。"

CONFIGS = [
    ("CPU 18 线程", ["-ngl", "0"]),
    ("CPU 单线程", ["-ngl", "0", "-t", "1"]),
    ("GPU 档（本机构建无 CUDA，会被忽略）", ["-ngl", "99"]),
]

SPEED_RE = re.compile(r"Prompt:\s*([\d.]+)\s*t/s\s*\|\s*Generation:\s*([\d.]+)\s*t/s")


def run(tag: str, extra: list[str]) -> tuple[str, str, str]:
    cmd = [str(EXE), "-m", str(MODEL), "-p", PROMPT, "-n", "1024", *extra, "-st"]
    print(f">> {tag}: {' '.join(extra)}")
    r = subprocess.run(cmd, capture_output=True, timeout=900)
    out = r.stdout.decode("utf-8", errors="replace") + r.stderr.decode("utf-8", errors="replace")
    m = SPEED_RE.search(out)
    speed = f"Prompt {m.group(1)} t/s | Generation {m.group(2)} t/s" if m else "（未取到速度行）"
    # 取思考链结束之后的正式回答（[End thinking] 之后的第一个非空行）
    body = out.split("[End thinking]")[-1] if "[End thinking]" in out else out
    answer = ""
    for line in body.splitlines():
        line = line.strip()
        if line and not line.startswith("[") and not line.startswith("Exiting"):
            answer = line
            break
    print(f"   {speed}")
    print(f"   {answer[:60]}")
    return speed, answer, out


def main() -> None:
    lines = [
        "Q3 推理速度对比",
        f"模型 : {MODEL.name}",
        f"二进制: llama.cpp b7 / commit c7fc509（MSVC 19.51.36252 编译）",
        f"命令 : llama-cli -m <model> -p \"{PROMPT}\" -n 1024 <档位> -st",
        f"时间 : {datetime.now():%Y-%m-%d %H:%M:%S}",
        "",
    ]
    results = {}
    for tag, extra in CONFIGS:
        speed, answer, raw = run(tag, extra)
        results[tag] = (speed, answer)
        lines += [
            f"===== {tag}  ({' '.join(extra)}) =====",
            f"速度: {speed}",
            f"回答: {answer}",
            "",
        ]
        (OUT.parent / f"raw_{extra[1] if extra[1].isdigit() else 'cpu'}.txt").write_text(
            raw, encoding="utf-8"
        )

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n[ok] -> {OUT}")


if __name__ == "__main__":
    main()
