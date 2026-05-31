"""
HUD overlay — leaderboard, countdown timer, and gift guide.

All elements live on the ManimGL main thread. The timer uses always_redraw
so it counts down smoothly between events. The leaderboard is rebuilt
explicitly whenever a score changes.
"""

import time as real_time

from manimlib import *

# Gift guide shown in bottom-left — edit to match your actual gift names.
GIFT_GUIDE = [
    ("🌹 Rose",        "earn a guess"),
    ("💙 Finger Heart", "reveal a hint"),
    ("🌌 Galaxy",      "auto-solve"),
    ("🌀 Universe",    "submit your equation"),
    ("💣 Bomb",        "throw a wrench"),
]


class HUD:
    def __init__(self, game_state, round_end_ref: list):
        """
        game_state      — shared GameState
        round_end_ref   — one-element list [float]; update to the new
                          deadline at the start of each round.
        """
        self.state         = game_state
        self.round_end_ref = round_end_ref
        self._leaderboard  = VGroup()
        self._gift_guide   = VGroup()
        self._timer        = None
        self._scene        = None

    def setup(self, scene):
        self._scene = scene

        self._timer = always_redraw(self._draw_timer)
        scene.add(self._timer)

        self._build_gift_guide()
        self.refresh_leaderboard()

    def refresh_leaderboard(self):
        if self._scene is None:
            return
        self._scene.remove(self._leaderboard)

        entries = self.state.leaderboard(8)

        title = Text("LEADERBOARD", font_size=20, color=BLUE_B)

        if entries:
            lines = [
                Text(f"{u}  {s}", font_size=20)
                for u, s in entries
            ]
        else:
            lines = [Text("no scores yet", font_size=18, color=GREY_B)]

        self._leaderboard = (
            VGroup(title, *lines)
            .arrange(DOWN, aligned_edge=LEFT, buff=0.15)
            .to_corner(UL, buff=0.4)
        )
        self._scene.add(self._leaderboard)

    # ── Private ───────────────────────────────────────────────────────

    def _build_gift_guide(self):
        title = Text("GIFTS", font_size=20, color=BLUE_B)
        rows  = [
            Text(f"{gift}  →  {action}", font_size=16, color=GREY_A)
            for gift, action in GIFT_GUIDE
        ]
        self._gift_guide = (
            VGroup(title, *rows)
            .arrange(DOWN, aligned_edge=LEFT, buff=0.12)
            .to_corner(DL, buff=0.4)
        )
        self._scene.add(self._gift_guide)

    def _draw_timer(self) -> Mobject:
        remaining = max(0.0, self.round_end_ref[0] - real_time.time())
        color = WHITE if remaining > 15 else YELLOW if remaining > 5 else RED
        return (
            Text(f"{remaining:.0f}s", font_size=40, color=color)
            .to_corner(UR, buff=0.4)
        )
