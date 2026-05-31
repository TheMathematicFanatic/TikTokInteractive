"""
Guess the Solution mode.

Gift tiers
──────────
GUESS           Buy one guess attempt.  Your next comment is your answer.
HINT            Play one step of the Solve timeline (reveals progress).
AUTO_SOLVE      Play the full Solve timeline, then start a new round.
CUSTOM_EQUATION Your next comment becomes the new equation for everyone.
WRENCH          Replace the current equation with a new random one.

Round lifecycle
───────────────
start_round → [viewers send gifts / type guesses] → first correct guess
              OR timeout → on_timeout → start_round (next equation)
"""

import random
import time as real_time

from manimlib import *
from MF_Algebra import *

from events import CommentEvent, GiftEvent, TikTokEvent
from game_state import GameState
from gifts import GiftTier, classify_gift
from modes.base import GameMode


# ── Equation pool ────────────────────────────────────────────────────────────

algebra_config["multiplication_mode"] = "auto"
algebra_config["always_color"] = {
    x: RED,    y: BLUE,   z: GREEN_E,
    a: RED_B,  b: GREEN_D, c: BLUE_E,
    n: GOLD,   m: BLUE_B,  w: PURPLE, p: PINK,
}

EQUATION_POOL: list = [
    x + 4    | 10,
    b + 7    | 10,
    10 - y   | 9,
    20 - a   | 15,
    5 * w    | 55,
    4 * z    | 40,
    10 * c   | 80,
    n * 2    | 14,
    87 + m   | 100,
    3 * p + 10 | 25,
]

ROUND_DURATION = 90   # seconds per round
EQ_SCALE       = 2.5  # auto_scale for all equation timelines


# ── Guess parsing ────────────────────────────────────────────────────────────

def parse_guess(text: str) -> float | None:
    """Extract a numeric guess from a comment string, or return None."""
    text = text.strip()
    # Strip leading "x=" / "y=" etc.
    if "=" in text:
        text = text.split("=")[-1].strip()
    text = text.replace(" ", "")
    try:
        return float(text)
    except ValueError:
        pass
    # Simple fraction e.g. "1/2"
    if "/" in text and text.count("/") == 1:
        try:
            num, den = text.split("/")
            return float(num) / float(den)
        except (ValueError, ZeroDivisionError):
            pass
    return None


# ── Mode ─────────────────────────────────────────────────────────────────────

class GuessingMode(GameMode):

    def __init__(self, scene, game_state: GameState, event_queue):
        super().__init__(scene, game_state, event_queue)
        self._eq_pool = list(EQUATION_POOL)
        random.shuffle(self._eq_pool)
        self._pool_index = 0

        # Round state — reset on each start_round()
        self.equation      = None   # current MF_Algebra expression
        self.eq_timeline   = None   # Evaluate timeline driving the display
        self.round_end     = 0.0    # real_time.time() deadline
        self.round_won     = False

        # Per-round viewer state
        self.pending_guessers: dict[str, int] = {}   # user → remaining guess tokens
        self.pending_eq_from:  str | None     = None  # user who may submit a custom equation

    # ── Public API ────────────────────────────────────────────────────

    def start_round(self, equation=None):
        self._clear_display()

        if equation is None:
            equation = self._next_equation()
        self.equation   = equation
        self.round_end  = real_time.time() + ROUND_DURATION
        self.round_won  = False
        self.pending_guessers.clear()
        self.pending_eq_from = None

        self.eq_timeline = Evaluate(auto_scale=EQ_SCALE)
        self.eq_timeline >> self.equation
        self.eq_timeline.mob.center()
        self.scene.play(Write(self.eq_timeline.mob))

    def handle_event(self, event: TikTokEvent):
        if self.round_won:
            return
        if isinstance(event, GiftEvent):
            self._handle_gift(event)
        elif isinstance(event, CommentEvent):
            self._handle_comment(event)

    def is_round_over(self) -> bool:
        return self.round_won or real_time.time() >= self.round_end

    def on_timeout(self):
        """Time ran out — reveal the answer, then cycle to next round."""
        self._reveal_answer(reason="Time's up!")
        self.scene.wait(2)
        self.start_round()

    # ── Gift handling ─────────────────────────────────────────────────

    def _handle_gift(self, event: GiftEvent):
        tier = classify_gift(event)

        if tier == GiftTier.GUESS:
            tokens = event.repeat_count  # sending 3 roses = 3 guess tokens
            self.pending_guessers[event.user] = (
                self.pending_guessers.get(event.user, 0) + tokens
            )
            print(f"[game] {event.user} earned {tokens} guess token(s)")

        elif tier == GiftTier.HINT:
            self._do_hint()

        elif tier == GiftTier.AUTO_SOLVE:
            self._do_auto_solve()

        elif tier == GiftTier.CUSTOM_EQUATION:
            self.pending_eq_from = event.user
            print(f"[game] {event.user} may now submit a custom equation")

        elif tier == GiftTier.WRENCH:
            self._do_wrench(event.user)

    # ── Comment handling ──────────────────────────────────────────────

    def _handle_comment(self, event: CommentEvent):
        # Custom equation submission takes priority
        if event.user == self.pending_eq_from:
            self._accept_custom_equation(event)
            return

        tokens = self.pending_guessers.get(event.user, 0)
        if tokens <= 0:
            return  # viewer hasn't bought a guess

        value = parse_guess(event.text)
        if value is None:
            return  # not a recognisable number — don't consume the token

        # Consume one token
        if tokens == 1:
            del self.pending_guessers[event.user]
        else:
            self.pending_guessers[event.user] = tokens - 1

        self.state.record_guess(event.user)
        self._do_guess(event.user, value)

    # ── Core actions ──────────────────────────────────────────────────

    def _do_guess(self, user: str, value: float):
        """Animate substitute + evaluate, award point on correct guess."""
        var = self.equation.get_all_variables().pop()
        mf_val = Smarten(int(value) if value == int(value) else value)

        self.eq_timeline >>= substitute_({var: mf_val}, maintain_color=True)
        self.eq_timeline.play_all(self.scene, wait_between=0.5)

        final  = self.eq_timeline.get_expression(-1)
        L, R   = final.children

        if L == R:
            self.scene.play(final.mob.animate.set_color(GREEN))
            self.scene.wait(1)
            self.state.award(user)
            self.round_won = True
            print(f"[game] {user} got it! Score: {self.state.scores[user].score}")
            self._reset_display(new_equation=False)
            self.start_round()
        else:
            self.scene.play(final.mob.animate.set_color(RED))
            self.scene.wait(1)
            self._reset_display(new_equation=True)

    def _do_hint(self):
        """Play one step of the Solve timeline as a hint."""
        solve_tl = Solve(auto_scale=EQ_SCALE)
        solve_tl >>= self.equation.copy()

        self.scene.play(FadeOut(self.eq_timeline.mob))
        solve_tl.mob.center()
        self.scene.add(solve_tl.mob)
        solve_tl.play_next(self.scene)
        self.scene.wait(2)
        self.scene.play(FadeOut(solve_tl.mob))
        self._rebuild_display()

    def _do_auto_solve(self):
        """Play the full Solve timeline, then start a new round."""
        solve_tl = Solve(auto_scale=EQ_SCALE)
        solve_tl >>= self.equation.copy()

        self.scene.play(FadeOut(self.eq_timeline.mob))
        solve_tl.mob.center()
        self.scene.add(solve_tl.mob)
        solve_tl.play_all(self.scene)
        self.scene.wait(2)

        self.round_won = True
        self._clear_display()
        self.start_round()

    def _do_wrench(self, gifter: str):
        """Replace the current equation with a fresh random one."""
        print(f"[game] {gifter} threw a wrench!")
        new_eq = self._random_equation()
        self._clear_display()
        self.equation   = new_eq
        self.round_end  = real_time.time() + ROUND_DURATION  # reset timer too
        self.pending_guessers.clear()

        self.eq_timeline = Evaluate(auto_scale=EQ_SCALE)
        self.eq_timeline >> self.equation
        self.eq_timeline.mob.center()
        self.scene.play(Write(self.eq_timeline.mob))

    def _accept_custom_equation(self, event: CommentEvent):
        self.pending_eq_from = None
        try:
            new_eq = text_to_MF_Algebra(event.text)
            if len(new_eq.get_all_variables()) == 0:
                raise ValueError("no variables")
            print(f"[game] Custom equation from {event.user}: {event.text}")
            self._clear_display()
            self.start_round(equation=new_eq)
        except Exception as exc:
            print(f"[game] Invalid equation '{event.text}' from {event.user}: {exc}")
            # Give the token back so they can try again
            self.pending_eq_from = event.user

    def _reveal_answer(self, reason: str = ""):
        """Show the solution without awarding a point (timeout path)."""
        if reason:
            print(f"[game] {reason}")
        solve_tl = Solve(auto_scale=EQ_SCALE)
        solve_tl >>= self.equation.copy()
        self.scene.play(FadeOut(self.eq_timeline.mob))
        solve_tl.mob.center()
        self.scene.add(solve_tl.mob)
        solve_tl.play_all(self.scene)
        self.scene.wait(1)
        self.scene.play(FadeOut(solve_tl.mob))
        self.eq_timeline = None

    # ── Display helpers ───────────────────────────────────────────────

    def _clear_display(self):
        if self.eq_timeline is not None and self.eq_timeline.mob in self.scene.mobjects:
            self.scene.play(FadeOut(self.eq_timeline.mob))
            self.eq_timeline = None

    def _rebuild_display(self):
        """Restore the original equation after a hint/guess animation."""
        self.eq_timeline = Evaluate(auto_scale=EQ_SCALE)
        self.eq_timeline >> self.equation.copy()
        self.eq_timeline.mob.center()
        self.scene.play(Write(self.eq_timeline.mob))

    def _reset_display(self, new_equation: bool):
        """After a guess animation: fade out and rewrite the equation."""
        self.scene.play(FadeOut(self.eq_timeline.mob))
        if new_equation:
            self._rebuild_display()
        else:
            self.eq_timeline = None

    # ── Equation generation ───────────────────────────────────────────

    def _next_equation(self):
        """Cycle through the pool, then generate random ones."""
        if self._pool_index < len(self._eq_pool):
            eq = self._eq_pool[self._pool_index]
            self._pool_index += 1
            return eq
        return self._random_equation()

    @staticmethod
    def _random_equation(depth: int = 2):
        return random_equation(depth)
