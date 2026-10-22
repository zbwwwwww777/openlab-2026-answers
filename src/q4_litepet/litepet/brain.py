"""LitePet 的"大脑"——纯逻辑，不依赖任何 GUI，方便单独跑单元测试。

负责三件事：
1. 判断当前处于一天中的哪个时段；
2. 根据时段 + 事件 + 好感度，决定宠物该说什么、心情如何；
3. 维护好感度/心情的演化规则。
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

# ---------------------------------------------------------------- 时段划分

PERIOD_NAMES: Dict[str, str] = {
    "morning": "清晨",
    "forenoon": "上午",
    "noon": "中午",
    "afternoon": "下午",
    "evening": "傍晚",
    "night": "深夜",
}

# 每个时段的行为参数：(移动速度倍率, 是否打瞌睡, 眨眼的活跃程度)
PERIOD_BEHAVIOR: Dict[str, Dict[str, float]] = {
    "morning":   {"speed": 1.2, "sleepy": 0.0, "blink": 1.0},
    "forenoon":  {"speed": 1.0, "sleepy": 0.0, "blink": 1.0},
    "noon":      {"speed": 0.6, "sleepy": 0.4, "blink": 0.7},
    "afternoon": {"speed": 1.1, "sleepy": 0.0, "blink": 1.0},
    "evening":   {"speed": 0.8, "sleepy": 0.1, "blink": 0.9},
    "night":     {"speed": 0.25, "sleepy": 1.0, "blink": 0.4},
}


def period_of(hour: int) -> str:
    """把 0~23 的小时数映射到时段名。"""
    if 5 <= hour < 9:
        return "morning"
    if 9 <= hour < 12:
        return "forenoon"
    if 12 <= hour < 14:
        return "noon"
    if 14 <= hour < 18:
        return "afternoon"
    if 18 <= hour < 23:
        return "evening"
    return "night"


def period_label(hour: Optional[int] = None) -> str:
    if hour is None:
        hour = datetime.now().hour
    return PERIOD_NAMES[period_of(hour)]


# ---------------------------------------------------------------- 台词库

LINES: Dict[str, Dict[str, List[str]]] = {
    "greet": {
        "morning":   ["早上好呀，今天也要元气满满！", "你醒啦？我等你等了好久。", "喵——伸个懒腰。"],
        "forenoon":  ["上午好，摸摸我的头再走？", "今天的任务清单写好了吗？", "阳光正好，适合发呆。"],
        "noon":      ["中午啦，记得吃饭。", "午饭吃什么？我闻闻……", "吃饱了就困，这是常态。"],
        "afternoon": ["下午好，要不要休息五分钟？", "嘿，别盯着屏幕看太久。", "我替你盯着时钟呢。"],
        "evening":   ["傍晚了，天色开始变温柔。", "晚上好，今天辛苦啦。", "该收收心准备收工了。"],
        "night":     ["这么晚还没睡？", "深夜是灵感最多的时候……也最伤身。", "我有点困了，你呢？"],
    },
    "click": {
        "morning":   ["喵！", "哎呀，戳我干嘛。", "再摸一下我就精神了。"],
        "forenoon":  ["干嘛干嘛，我在思考人生。", "再点一下试试？", "嘿嘿，痒。"],
        "noon":      ["别闹，我困。", "（打了个哈欠）", "陪我躺一会儿嘛。"],
        "afternoon": ["你终于理我了。", "喵呜～", "手感怎么样？"],
        "evening":   ["抱抱。", "今天过得还行吗？", "蹭蹭你。"],
        "night":     ["嘘——小声点。", "再熬夜你就要掉头发了。", "我陪你，但你不许太晚。"],
    },
    "idle": {
        "morning":   ["今天会有好事发生吧。", "窗外有鸟在叫。"],
        "forenoon":  ["代码是人类写给计算机的诗。", "我在数你的键盘声。"],
        "noon":      ["……Zzz", "好想睡个午觉。"],
        "afternoon": ["你敲键盘的节奏挺好听。", "我在你的桌角上散步。"],
        "evening":   ["天黑了，我也该安静一点。", "要不要听首歌？"],
        "night":     ["夜深了，早点休息吧。", "……Zzz"],
    },
    "fed": ["谢谢！这是今天最开心的事。", "好吃！我还能再吃一点吗？", "你最好了。"],
}

# 回来寒暄：按离开的分钟数分级
BACK_LINES = [
    (2, "你只是眨了下眼就回来了？"),
    (30, "你回来啦，我还以为你跑了。"),
    (180, "你终于回来了，我数了你好久。"),
    (1440, "好久不见……我都快不认识你了。"),
]

MOOD_TABLE = [
    (20, "有点怕生"),
    (40, "还算亲近"),
    (60, "很熟了"),
    (80, "形影不离"),
    (101, "这辈子跟你了"),
]


# ---------------------------------------------------------------- 状态


@dataclass
class PetState:
    """会被持久化的那部分状态。"""

    name: str = "小灯"
    affinity: int = 10          # 好感度 0-100
    total_clicks: int = 0
    total_feeds: int = 0
    pos: Dict[str, int] = field(default_factory=lambda: {"x": 200, "y": 200})
    history: List[str] = field(default_factory=list)   # 最近说过的几句话
    last_seen: str = ""
    theme: str = "mint"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "affinity": self.affinity,
            "total_clicks": self.total_clicks,
            "total_feeds": self.total_feeds,
            "pos": dict(self.pos),
            "history": list(self.history),
            "last_seen": self.last_seen,
            "theme": self.theme,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PetState":
        st = cls()
        st.name = data.get("name", st.name)
        st.affinity = int(data.get("affinity", st.affinity))
        st.total_clicks = int(data.get("total_clicks", 0))
        st.total_feeds = int(data.get("total_feeds", 0))
        pos = data.get("pos") or {}
        st.pos = {"x": int(pos.get("x", 200)), "y": int(pos.get("y", 200))}
        st.history = list(data.get("history", []))
        st.last_seen = data.get("last_seen", "")
        st.theme = data.get("theme", st.theme)
        return st


class Brain:
    """把"时间 + 事件 + 好感度"翻译成一句话。"""

    MAX_HISTORY = 20

    def __init__(self, state: PetState, seed: Optional[int] = None) -> None:
        self.state = state
        self._rng = random.Random(seed)

    # ---------------- 好感度

    def add_affinity(self, delta: int) -> None:
        self.state.affinity = max(0, min(100, self.state.affinity + delta))

    @property
    def mood(self) -> str:
        for threshold, label in MOOD_TABLE:
            if self.state.affinity < threshold:
                return label
        return MOOD_TABLE[-1][1]

    # ---------------- 说话

    def _pick(self, pool: List[str]) -> str:
        return self._rng.choice(pool)

    def say(self, event: str, now: Optional[datetime] = None) -> str:
        """按事件挑一句话；同时记入历史。"""
        now = now or datetime.now()
        period = period_of(now.hour)
        entry = LINES.get(event)
        if isinstance(entry, dict):
            # 按时段分桶的台词
            pool = entry.get(period) or entry.get("forenoon") or LINES["idle"][period]
        else:
            # 不区分时段的台词（比如"被喂了"）
            pool = entry or LINES["idle"][period]
        line = self._pick(pool)
        self.remember(line)
        return line

    def greet_back(self, now: Optional[datetime] = None) -> str:
        """根据上次离开的时长，说一句"你回来了"。"""
        now = now or datetime.now()
        if not self.state.last_seen:
            line = self.say("greet", now)
            return line
        try:
            last = datetime.fromisoformat(self.state.last_seen)
        except ValueError:
            return self.say("greet", now)

        minutes = max(0.0, (now - last).total_seconds() / 60.0)
        for limit, text in BACK_LINES:
            if minutes < limit:
                line = text
                break
        else:
            line = "你消失了好久好久……"
        self.remember(line)
        return line

    def feed(self) -> str:
        self.add_affinity(6)
        self.state.total_feeds += 1
        return self.say("fed")

    def poke(self) -> str:
        self.add_affinity(1)
        self.state.total_clicks += 1
        return self.say("click")

    def idle(self, now: Optional[datetime] = None) -> str:
        return self.say("idle", now)

    def remember(self, line: str) -> None:
        self.state.history.append(line)
        if len(self.state.history) > self.MAX_HISTORY:
            self.state.history = self.state.history[-self.MAX_HISTORY:]

    # ---------------- 行为参数

    def behavior(self, now: Optional[datetime] = None) -> Dict[str, float]:
        now = now or datetime.now()
        base = dict(PERIOD_BEHAVIOR[period_of(now.hour)])
        # 好感度越高越活泼
        base["speed"] *= 0.7 + self.state.affinity / 200.0
        return base

    def is_sleepy(self, now: Optional[datetime] = None) -> bool:
        now = now or datetime.now()
        return self.behavior(now)["sleepy"] >= 0.5
