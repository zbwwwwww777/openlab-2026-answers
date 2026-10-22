"""LitePet 的持久化层——关掉程序再打开，它还记得你。

存成一个 JSON 文件，默认放在用户目录下（Windows: %USERPROFILE%\\.litepet\\state.json）。
写入采用"先写临时文件再原子替换"的策略，避免崩溃时把存档写坏。
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional

from .brain import PetState

LOG = logging.getLogger("litepet.memory")

DEFAULT_DIR = Path(os.path.expanduser("~")) / ".litepet"
STATE_FILE = "state.json"
LOG_FILE = "pet.log"


def ensure_dir(base: Optional[Path] = None) -> Path:
    """保证存档目录存在，返回它。"""
    base = Path(base) if base else DEFAULT_DIR
    base.mkdir(parents=True, exist_ok=True)
    return base


def setup_logging(base: Optional[Path] = None, level: int = logging.INFO) -> Path:
    """把日志同时写进文件和 stderr，日志文件路径返回给调用方展示。"""
    base = ensure_dir(base)
    log_path = base / LOG_FILE
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(fmt)

    root = logging.getLogger("litepet")
    root.setLevel(level)
    if not any(isinstance(h, logging.FileHandler) for h in root.handlers):
        root.addHandler(file_handler)
    if not any(h.stream is not None and getattr(h, "stream", None) is not None
               and getattr(h.stream, "name", "") == "<stderr>" for h in root.handlers):
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(fmt)
        root.addHandler(stream_handler)
    return log_path


class Memory:
    """读写宠物档案。"""

    def __init__(self, base: Optional[Path] = None) -> None:
        self.base = ensure_dir(base)
        self.path = self.base / STATE_FILE

    # ---------------- 读

    def load(self) -> PetState:
        if not self.path.exists():
            LOG.info("没有找到存档，创建一只新的宠物：%s", self.path)
            return PetState()
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            state = PetState.from_dict(data)
            LOG.info("读取存档成功：好感度=%d，上次见面=%s",
                     state.affinity, state.last_seen or "(从未)")
            return state
        except (json.JSONDecodeError, OSError, TypeError, ValueError) as exc:
            # 存档坏了也不能让宠物打不开，直接用默认值，坏的存档留个备份
            LOG.warning("存档损坏（%s），已备份为 state.json.bak 并重置", exc)
            try:
                self.path.replace(self.path.with_suffix(".json.bak"))
            except OSError:
                pass
            return PetState()

    # ---------------- 写

    def save(self, state: PetState, now: Optional[datetime] = None) -> None:
        state.last_seen = (now or datetime.now()).isoformat(timespec="seconds")
        payload = state.to_dict()
        try:
            # 原子写：先写临时文件，再整体替换
            fd, tmp_name = tempfile.mkstemp(dir=str(self.base), suffix=".tmp")
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            os.replace(tmp_name, self.path)
            LOG.debug("存档已写入 %s", self.path)
        except OSError as exc:
            LOG.error("写存档失败：%s", exc)

    def reset(self) -> None:
        try:
            if self.path.exists():
                self.path.unlink()
                LOG.info("存档已删除")
        except OSError as exc:
            LOG.error("删除存档失败：%s", exc)

    @property
    def exists(self) -> bool:
        return self.path.exists()
