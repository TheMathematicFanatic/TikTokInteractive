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
"""

import queue
import time as real_time
import traceback

from manimlib import *

from game_state import GameState
from hud import HUD
from listener import start_listener
from modes.guessing import GuessingMode
from repl import start_repl


class TikTokGameScene(Scene):

    # Set via command-line or subclass — the TikTok username to connect to.
    tiktok_username: str = "@your_username"

    def construct(self):
        self.event_queue   = queue.Queue()
        self.command_queue = queue.Queue()
        self.game_state    = GameState()

        # round_end_ref is a one-element list so the HUD timer closure
        # always reads the live deadline without needing a lambda capture trick.
        self.round_end_ref = [real_time.time() + 9999]

        self.hud = HUD(self.game_state, self.round_end_ref)
        self.hud.setup(self)

        self.mode = GuessingMode(self, self.game_state, self.event_queue)

        # Start listening (no-op if TikTokLive isn't installed yet)
        start_listener(self.tiktok_username, self.event_queue)

        # Background REPL: lines typed in the terminal land on command_queue
        start_repl(self.command_queue)

        self.mode.start_round()
        self._game_loop()

    # ── Main loop ─────────────────────────────────────────────────────

    def _game_loop(self):
        while not self.is_window_closing():
            self._sync_round_end()

            # Keep the window live and updaters running until an event
            # arrives or the round timer fires.
            self.wait_until(
                lambda: not self.event_queue.empty()
                        or not self.command_queue.empty()
                        or self.mode.is_round_over(),
                max_time=max(0.5, self.round_end_ref[0] - real_time.time() + 0.1),
            )

            if self.mode.is_round_over():
                self.mode.on_timeout()
                self._sync_round_end()
                self.hud.refresh_leaderboard()

            # Drain all queued events — each may block for an animation.
            while not self.event_queue.empty():
                if self.is_window_closing():
                    return
                event = self.event_queue.get_nowait()
                self.mode.handle_event(event)
                self._sync_round_end()
                # Refresh leaderboard after any event that could score a point.
                self.hud.refresh_leaderboard()

            # Drain typed commands from the terminal REPL.
            while not self.command_queue.empty():
                if self.is_window_closing():
                    return
                self._run_command(self.command_queue.get_nowait())
                self._sync_round_end()

    def _run_command(self, line):
        """Exec a line typed in the REPL, with the manimlib namespace + self."""
        from manimlib import __dict__ as manim_ns
        env = {**manim_ns, "self": self}
        try:
            try:
                print(repr(eval(line, env)))
            except SyntaxError:
                exec(line, env)
        except Exception:
            traceback.print_exc()

    def _sync_round_end(self):
        """Keep the HUD timer in sync with the mode's current deadline."""
        if hasattr(self.mode, "round_end"):
            self.round_end_ref[0] = self.mode.round_end
