#!/usr/bin/env python3
"""把 答卷.md 导出成投递用的 PDF。

做法：markdown -> HTML（带打印样式）-> Edge 无头模式打印成 PDF。
用浏览器渲染而不是别的库，是因为中文字体、表格、代码块这些交给排版引擎最稳。

用法：
    python tools/export_pdf.py                 # 输出到 dist/
    python tools/export_pdf.py --out 路径.pdf
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import markdown

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DEFAULT_MD = ROOT / "答卷.md"

# Edge 的常见安装位置
EDGE_CANDIDATES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]

CSS = """
@page { size: A4; margin: 18mm 16mm; }
* { box-sizing: border-box; }
body {
    font-family: "Microsoft YaHei", "PingFang SC", "Segoe UI", sans-serif;
    font-size: 10.5pt;
    line-height: 1.75;
    color: #1a1a1a;
    max-width: 100%;
    margin: 0 auto;
}
h1 { font-size: 20pt; text-align: center; margin: 0 0 18pt; padding-bottom: 10pt;
     border-bottom: 2.5pt solid #2f4858; }
h2 { font-size: 15pt; margin: 0 0 12pt; padding: 6pt 10pt;
     background: #eef4f8; border-left: 5pt solid #2f4858;
     page-break-before: always; page-break-after: avoid; }
h2:first-of-type { page-break-before: auto; }
h3 { font-size: 12.5pt; margin: 14pt 0 8pt; color: #2f4858;
     page-break-after: avoid; }
h4 { font-size: 11pt; margin: 12pt 0 6pt; color: #3d5a6c;
     page-break-after: avoid; }
p { margin: 6pt 0; }
ul, ol { margin: 6pt 0 6pt 18pt; padding-left: 8pt; }
li { margin: 2pt 0; }
blockquote {
    margin: 8pt 0; padding: 6pt 12pt; background: #f7f9fb;
    border-left: 3.5pt solid #9db4d6; color: #333;
}
blockquote p { margin: 2pt 0; }
code {
    font-family: Consolas, "Courier New", monospace;
    font-size: 9pt; background: #f2f4f6; padding: 1pt 3pt;
    border-radius: 2pt;
}
pre {
    background: #f6f8fa; border: 1px solid #dde2e7; border-radius: 3pt;
    padding: 8pt 10pt; margin: 8pt 0;
    page-break-inside: avoid;
}
pre code {
    display: block; background: none; padding: 0;
    font-size: 8.5pt; line-height: 1.55;
    white-space: pre-wrap; word-break: break-all;
}
table {
    border-collapse: collapse; width: 100%; margin: 10pt 0;
    font-size: 9pt; page-break-inside: avoid;
}
th, td { border: 1px solid #c9d2da; padding: 5pt 7pt; text-align: left; }
th { background: #eef4f8; font-weight: 600; }
tbody tr:nth-child(even) { background: #fafbfc; }
img { max-width: 100%; display: block; margin: 8pt auto;
      border: 1px solid #dde2e7; page-break-inside: avoid; }
kbd { background: #fff4ce; border: 1px solid #e0c96a; border-radius: 2pt;
      padding: 0 3pt; font-size: 8.5pt; color: #7a5c00; }
hr { border: none; border-top: 1px solid #dde2e7; margin: 14pt 0; }
a { color: #1a5fb4; text-decoration: none; }
center { display: block; text-align: center; font-size: 8.5pt;
         color: #666; margin: 2pt 0 10pt; }
"""


def build_html(md_path: Path) -> Path:
    text = md_path.read_text(encoding="utf-8")
    body = markdown.markdown(
        text,
        extensions=["tables", "fenced_code", "codehilite", "sane_lists", "nl2br"],
        extension_configs={"codehilite": {"guess_lang": False}},
    )
    html = (
        "<!DOCTYPE html>\n<html lang=\"zh-CN\">\n<head>\n"
        "<meta charset=\"utf-8\">\n"
        "<title>OpenLab 2026 纳新笔试答卷</title>\n"
        f"<style>{CSS}</style>\n</head>\n<body>\n{body}\n</body>\n</html>\n"
    )
    out = md_path.with_suffix(".html")
    out.write_text(html, encoding="utf-8")
    return out


def find_edge() -> Path:
    for c in EDGE_CANDIDATES:
        p = Path(c)
        if p.exists():
            return p
    raise SystemExit("找不到 Edge 浏览器，无法打印 PDF")


def print_pdf(edge: Path, html: Path, pdf: Path) -> None:
    pdf.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        str(edge),
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf}",
        html.as_uri(),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if not pdf.exists():
        raise SystemExit(f"PDF 生成失败：{r.stdout}\n{r.stderr}")
    print(f"[ok] PDF -> {pdf}  ({pdf.stat().st_size / 1024:.0f} KB)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", default=str(DEFAULT_MD))
    ap.add_argument("--out", default=str(ROOT.parent / "dist" / "202600130217_张博文_Openlab初试.pdf"))
    args = ap.parse_args()

    md_path = Path(args.md)
    print(f"源 : {md_path}")
    html = build_html(md_path)
    print(f"HTML: {html}")
    print_pdf(find_edge(), html, Path(args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
