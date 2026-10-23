#!/usr/bin/env python3
"""第 3 题加分项：跑一遍 llama-server + HTTP 调用，把证据落成 UTF-8 文件。

之前 3.6.1 里引用的计时数字只在当时的终端输出里出现过，没存盘；这里重新跑一次，
把 HTTP 状态、耗时、返回内容和服务端计时全部写进文件，避免"无据可查"。

注意：本机设了 http_proxy，请求 127.0.0.1 必须显式绕过代理，否则会拿 502。

用法：
    python tools/bench_server.py
产出：
    res/q3_evidence/server_evidence.txt
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "res" / "q3_evidence" / "server_evidence.txt"

EXE = Path(r"C:\Users\lennovo\dev\llm\llama.cpp\build\bin\llama-server.exe")
MODEL = Path(r"C:\Users\lennovo\Downloads\gemma-4-E2B-it-Q4_0.gguf")
URL = "http://127.0.0.1:8080"

# 关键：绕过系统代理，否则 127.0.0.1 也会被发给代理（会拿到 502）
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def wait_ready(timeout: int = 120) -> bool:
    for _ in range(timeout):
        try:
            with opener.open(f"{URL}/health", timeout=2) as r:
                if b"ok" in r.read():
                    return True
        except Exception:
            time.sleep(1)
    return False


def main() -> int:
    print("启动 llama-server ...")
    proc = subprocess.Popen(
        [str(EXE), "-m", str(MODEL), "--port", "8080", "-ngl", "0"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    try:
        if not wait_ready():
            print("server 未就绪", file=sys.stderr)
            return 1

        body = json.dumps(
            {
                "model": "gemma",
                "messages": [
                    {"role": "user", "content": "用一句话解释什么是版本控制系统 Git。"}
                ],
            },
            ensure_ascii=False,
        ).encode("utf-8")

        print("发送 POST /v1/chat/completions ...")
        t0 = time.time()
        req = urllib.request.Request(
            f"{URL}/v1/chat/completions",
            data=body,
            headers={"Content-Type": "application/json"},
        )
        with opener.open(req, timeout=600) as r:
            status = r.status
            payload = r.read().decode("utf-8", errors="replace")
        elapsed = time.time() - t0

        resp = json.loads(payload)
        content = resp["choices"][0]["message"]["content"]
        usage = resp.get("usage", {})
        print(f"HTTP {status}  耗时 {elapsed:.1f}s  usage={usage}")
        print(content[:80])
    finally:
        proc.terminate()
        try:
            server_log = proc.communicate(timeout=30)[0] or ""
        except subprocess.TimeoutExpired:
            proc.kill()
            server_log = proc.communicate()[0] or ""

    timings = [
        line.strip()
        for line in server_log.splitlines()
        if re.search(r"tokens per second|eval time|prompt eval|total time", line)
    ]

    lines = [
        "Q3 加分项：llama-server + HTTP 接口调用",
        f"命令 : llama-server.exe -m {MODEL.name} --port 8080 -ngl 0",
        f"请求 : POST {URL}/v1/chat/completions",
        "",
        f"HTTP 状态 : {status}",
        f"耗时      : {elapsed:.1f} s",
        f"usage     : {usage}",
        "",
        "返回内容：",
        content,
        "",
        "服务端计时（来自 llama-server 自己的输出）：",
        *(timings or ["（未捕获到计时行）"]),
    ]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n[ok] -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
