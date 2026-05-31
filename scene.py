"""
TikTokGameScene — the ManimGL scene.

Responsibilities
────────────────
- Own the event queue (the only object shared with the listener thread).
- Run the main wait_until → drain-queue → handle-event loop.
- Let the active GameMode drive all animation logic.
- Refresh the HUD when game state changes.

The listener thread ONLY ever calls event_queue.put().
Everything else (MF_Algebra, Manim, game state) lives here on the main thread.

Test keys (no TikTok connection needed)
────────────────────────────────────────
  G   — gift: earn a guess token (like sending a Rose)
  C   — gift + correct comment: auto-solves then types the right answer
  X   — gift + wrong comment: types solution + 1
  H   — gift: hint (one Solve step)
  S   — gift: auto-solve
  W   — gift: wrench (replace equation)
"""

import queue
import time as real_time

from manimlib import *

from events import CommentEvent, GiftEvent
from game_state import GameState
from gifts import GIFT_TIERS, GiftTier
from hud import HUD
from listener import start_listener
from modes.guessing import GuessingMode

TEST_USER = "TestViewer"

# Grab a gift name for each tier so we don't hard-code strings here.
_tier_to_name = {v: k for k, v in GIFT_TIERS.items()}


def _gift(tier: GiftTier) -> GiftEvent:
    return GiftEvent(user=TEST_USER, gift_name=_tier_to_name[tier], diamonds=1)


class TikTokGameScene(Scene):

    tiktok_username: str = "@your_username"

    def construct(self):
        self.event_queue   = queue.Queue()
        self.game_state    = GameState()
        self.round_end_ref = [real_time.time() + 9999]

        self.hud = HUD(self.game_state, self.round_end_ref)
        self.hud.setup(self)

        self.mode = GuessingMode(self, self.game_state, self.event_queue)

        start_listener(self.tiktok_username, self.event_queue)
        self._register_test_keys()

        self.mode.start_round()
        self._game_loop()

    # ── Main loop ─────────────────────────────────────────────────────

    def _game_loop(self):
        while not self.is_window_closing():
            self._sync_round_end()

            self.wait_until(
                lambda: not self.event_queue.empty() or self.mode.is_round_over(),
                max_time=max(0.5, self.round_end_ref[0] - real_time.time() + 0.1),
            )

            if self.mode.is_round_over():
                self.mode.on_timeout()
                self._sync_round_end()
                self.hud.refresh_leaderboard()

            while not self.event_queue.empty():
                if self.is_window_closing():
                    return
                event = self.event_queue.get_nowait()
                self.mode.handle_event(event)
                self._sync_round_end()
                self.hud.refresh_leaderboard()

    # ── Test key bindings ─────────────────────────────────────────────

    def _register_test_keys(self):
        try:
            from pyglet.window import key as K
        except ImportError:
            return

        q = self.event_queue

        print("\nTest keys:")
        print("  G  —  earn a guess token")
        print("  C  —  token + correct answer")
        print("  X  —  token + wrong answer")
        print("  H  —  hint gift")
        print("  S  —  auto-solve gift")
        print("  W  —  wrench gift\n")

        scene = self

        @self.window._window.event
        def on_key_press(symbol, modifiers):
            if symbol == K.G:
                q.put(_gift(GiftTier.GUESS))

            elif symbol == K.H:
                q.put(_gift(GiftTier.HINT))

            elif symbol == K.S:
                q.put(_gift(GiftTier.AUTO_SOLVE))

            elif symbol == K.W:
                q.put(_gift(GiftTier.WRENCH))

            elif symbol in (K.C, K.X):
                val = scene._current_solution()
                if val is None:
                    return
                guess = val if symbol == K.C else val + 1
                q.put(_gift(GiftTier.GUESS))
                q.put(CommentEvent(user=TEST_USER, text=str(guess)))

    def _current_solution(self):
        """Silently compute the solution for the current equation."""
        try:
            from MF_Algebra import Solve
            eq  = self.mode.equation
            if eq is None:
                return None
            tl  = Solve()
            tl >>= eq.copy()
            return int(tl.solution.compute())
        except Exception:
            return None

    def _sync_round_end(self):
        if hasattr(self.mode, "round_end"):
            self.round_end_ref[0] = self.mode.round_end
