"""
HUD overlay — leaderboard and countdown timer.

Both live on the ManimGL main thread. The timer uses always_redraw so it
counts down smoothly between events without any extra work.  The leaderboard
is rebuilt explicitly whenever a score changes.
"""

import time as real_time

from manimlib import *


class HUD:
    def __init__(self, game_state, round_end_ref: list):
        """
        game_state      — shared GameState
        round_end_ref   — a one-element list [float] so the timer closure
                          always reads the current round's deadline.
                          Update round_end_ref[0] at the start of each round.
        """
        self.state          = game_state
        self.round_end_ref  = round_end_ref
        self._leaderboard   = VGroup()
        self._timer         = None
        self._scene         = None

    def setup(self, scene):
        self._scene = scene

        self._timer = always_redraw(self._draw_timer)
        scene.add(self._timer)

        self.refresh_leaderboard()

    def refresh_leaderboard(self):
        if self._scene is None:
            return
        self._scene.remove(self._leaderboard)

        entries = self.state.leaderboard(8)
        if not entries:
            self._leaderboard = VGroup()
            return

        lines = [Text(f"{u}:  {s}", font_size=22) for u, s in entries]
        self._leaderboard = (
            VGroup(*lines)
            .arrange(DOWN, aligned_edge=LEFT, buff=0.15)
            .to_corner(UL, buff=0.4)
        )
        self._scene.add(self._leaderboard)

    # ── Private ───────────────────────────────────────────────────────

    def _draw_timer(self) -> Mobject:
        remaining = max(0.0, self.round_end_ref[0] - real_time.time())
        color = WHITE if remaining > 15 else YELLOW if remaining > 5 else RED
        return (
            Text(f"{remaining:.0f}s", font_size=40, color=color)
            .to_corner(UR, buff=0.4)
        )
