"""LitePet 的单元测试（纯逻辑部分，不需要图形界面）。

    python -m unittest discover -s tests
    或者：python tests/test_brain.py
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from litepet.brain import Brain, PetState, period_of  # noqa: E402
from litepet.memory import Memory  # noqa: E402


class TestPeriod(unittest.TestCase):
    def test_boundaries(self):
        cases = {
            0: "night", 4: "night",
            5: "morning", 8: "morning",
            9: "forenoon", 11: "forenoon",
            12: "noon", 13: "noon",
            14: "afternoon", 17: "afternoon",
            18: "evening", 22: "evening",
            23: "night",
        }
        for hour, expected in cases.items():
            self.assertEqual(period_of(hour), expected, f"hour={hour}")

    def test_all_hours_covered(self):
        for h in range(24):
            self.assertIn(period_of(h),
                          {"morning", "forenoon", "noon", "afternoon", "evening", "night"})


class TestState(unittest.TestCase):
    def test_roundtrip(self):
        st = PetState(name="小花", affinity=42, total_clicks=7, total_feeds=3,
                      pos={"x": 111, "y": 222}, history=["喵"], theme="peach")
        restored = PetState.from_dict(json.loads(json.dumps(st.to_dict())))
        self.assertEqual(restored.name, "小花")
        self.assertEqual(restored.affinity, 42)
        self.assertEqual(restored.pos, {"x": 111, "y": 222})
        self.assertEqual(restored.theme, "peach")

    def test_from_empty_dict(self):
        st = PetState.from_dict({})
        self.assertEqual(st.affinity, 10)
        self.assertEqual(st.theme, "mint")


class TestBrain(unittest.TestCase):
    def setUp(self):
        self.state = PetState()
        self.brain = Brain(self.state, seed=1)

    def test_affinity_clamped(self):
        self.brain.add_affinity(-999)
        self.assertEqual(self.state.affinity, 0)
        self.brain.add_affinity(999)
        self.assertEqual(self.state.affinity, 100)

    def test_mood_thresholds(self):
        for value, expected in [(0, "有点怕生"), (25, "还算亲近"), (45, "很熟了"),
                                (65, "形影不离"), (95, "这辈子跟你了")]:
            self.state.affinity = value
            self.assertEqual(self.brain.mood, expected)

    def test_poke_and_feed(self):
        before = self.state.affinity
        line = self.brain.poke()
        self.assertIsInstance(line, str)
        self.assertGreater(len(line), 0)
        self.assertEqual(self.state.affinity, before + 1)
        self.assertEqual(self.state.total_clicks, 1)

        self.brain.feed()
        self.assertEqual(self.state.total_feeds, 1)
        self.assertEqual(self.state.affinity, before + 7)

    def test_history_capped(self):
        for _ in range(50):
            self.brain.poke()
        self.assertLessEqual(len(self.state.history), Brain.MAX_HISTORY)
        self.assertEqual(self.state.total_clicks, 50)

    def test_greet_back_levels(self):
        now = datetime(2026, 10, 20, 10, 0, 0)
        for minutes, keyword in [(1, "眨了下眼"), (10, "跑了"), (60, "数了你好久"),
                                 (600, "好久不见")]:
            self.state.last_seen = (now - timedelta(minutes=minutes)).isoformat()
            text = self.brain.greet_back(now)
            self.assertIn(keyword, text)

    def test_greet_back_no_history(self):
        self.state.last_seen = ""
        self.assertTrue(self.brain.greet_back())

    def test_behavior_night_is_slow_and_sleepy(self):
        night = self.brain.behavior(datetime(2026, 10, 20, 2, 0))
        noon = self.brain.behavior(datetime(2026, 10, 20, 10, 0))
        self.assertLess(night["speed"], noon["speed"])
        self.assertTrue(self.brain.is_sleepy(datetime(2026, 10, 20, 2, 0)))
        self.assertFalse(self.brain.is_sleepy(datetime(2026, 10, 20, 10, 0)))

    def test_deterministic_with_seed(self):
        b1 = Brain(PetState(), seed=7)
        b2 = Brain(PetState(), seed=7)
        self.assertEqual(b1.poke(), b2.poke())


class TestMemory(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.memory = Memory(Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def test_first_load_creates_default(self):
        st = self.memory.load()
        self.assertFalse(self.memory.exists)
        self.assertEqual(st.affinity, 10)

    def test_save_then_load(self):
        st = self.memory.load()
        st.name = "小灯"
        st.affinity = 55
        st.pos = {"x": 640, "y": 360}
        self.memory.save(st, now=datetime(2026, 10, 20, 12, 0, 0))

        reloaded = self.memory.load()
        self.assertEqual(reloaded.name, "小灯")
        self.assertEqual(reloaded.affinity, 55)
        self.assertEqual(reloaded.pos, {"x": 640, "y": 360})
        self.assertEqual(reloaded.last_seen, "2026-10-20T12:00:00")

    def test_corrupted_file_falls_back(self):
        self.memory.path.write_text("{这不是合法 JSON", encoding="utf-8")
        st = self.memory.load()
        self.assertEqual(st.affinity, 10)   # 不能崩，直接给默认值

    def test_reset(self):
        st = self.memory.load()
        self.memory.save(st)
        self.assertTrue(self.memory.exists)
        self.memory.reset()
        self.assertFalse(self.memory.exists)


if __name__ == "__main__":
    unittest.main(verbosity=2)
