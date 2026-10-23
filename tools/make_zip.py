#!/usr/bin/env python3
"""把源文件与图片打包成投递用的 zip。

提交须知：「PDF 交单个文件；其他格式连同源文件和图片打包成.zip」
所以这个包里放：答卷源文件（.md）、各题源码、截图与录屏、编译/运行证据。
不放：.git、__pycache__、编译产物（*.obj/*.pdb/*.exe）、导出用的中间 HTML。

用法：
    python tools/make_zip.py
产出：
    dist/202600130217_张博文_Openlab初试.zip
"""

from __future__ import annotations

import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT.parent / "dist" / "202600130217_张博文_Openlab初试.zip"

# 不进包的东西
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", "dist"}
SKIP_SUFFIX = {".pyc", ".obj", ".pdb", ".ilk", ".exe", ".html", ".pyo"}


def wanted(p: Path) -> bool:
    if any(part in SKIP_DIRS for part in p.parts):
        return False
    if p.suffix.lower() in SKIP_SUFFIX:
        return False
    return p.is_file()


def main() -> None:
    files = sorted(
        (p for p in ROOT.rglob("*") if wanted(p)),
        key=lambda p: p.relative_to(ROOT).as_posix(),
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    total = 0
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for f in files:
            rel = f.relative_to(ROOT).as_posix()
            z.write(f, f"openlab-answers/{rel}")
            total += f.stat().st_size

    print(f"[ok] {OUT}")
    print(f"     文件 {len(files)} 个，原始 {total / 1024 / 1024:.1f} MB"
          f" -> 压缩后 {OUT.stat().st_size / 1024 / 1024:.1f} MB")
    print()
    print("包内清单：")
    with zipfile.ZipFile(OUT) as z:
        for n in z.namelist():
            size = z.getinfo(n).file_size
            if size > 200 * 1024:
                print(f"  {n}  ({size / 1024 / 1024:.1f} MB)")


if __name__ == "__main__":
    main()
