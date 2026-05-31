# TikTokInteractive

Interactive TikTok live stream where viewers send gifts to interact with a ManimGL algebra scene powered by the MF_Algebra CAS library.

## What this is

A ManimGL scene that listens to a live TikTok stream and animates algebraic transformations in response to viewer gifts and comments. The first game mode is **Guess the Solution** — an equation is displayed and viewers send gifts to earn guess attempts, hints, or trigger special effects.

## Stack

- **ManimGL** (not Manim CE) — real-time OpenGL rendering
- **MF_Algebra** (`pip install MF_Algebra`) — John Connell's CAS library for animated algebra. Expressions, Actions, and Timelines compose via `>>`. Key classes: `Evaluate`, `Solve`, `substitute_`, `evaluate_`, `text_to_MF_Algebra`, `random_equation`.
- **TikTokLive** — unofficial websocket listener for TikTok live events
- **Python threading + queue.Queue** — the only cross-thread boundary; listener thread puts events in, main thread drains them

## Architecture

```
listener.py (background thread)          scene.py (ManimGL main thread)
  TikTokLive async client          →      queue.Queue (thread-safe)
  on_comment / on_gift             →      _game_loop: wait_until → drain → handle
                                          mode.handle_event(event) → scene.play(...)
```

**The core loop** in `scene.py` uses `self.wait_until(condition, max_time)` — this keeps the OpenGL window live, runs updaters (HUD timer), and dispatches OS events while blocking Python until an event arrives or the round times out. Never use `input()` or raw `queue.get()` — that freezes the window.

**Thread safety rule:** the listener thread only ever calls `event_queue.put()`. All MF_Algebra expressions, Manim mobjects, and game state are touched exclusively on the main thread.

## File structure

```
main.py                  # entry point — subclass TikTokGameScene, set tiktok_username
scene.py                 # TikTokGameScene: owns queue, HUD, mode, game loop
listener.py              # TikTokLive thread → queue
events.py                # CommentEvent, GiftEvent dataclasses
gifts.py                 # GiftTier enum + classify_gift(); edit GIFT_TIERS dict to match real gift names
game_state.py            # GameState: scores, leaderboard; round state stays in the mode
hud.py                   # HUD: always_redraw timer (top-right), rebuilt leaderboard (top-left)
modes/
  base.py                # GameMode ABC: start_round, handle_event, is_round_over, on_timeout
  guessing.py            # GuessingMode — Guess the Solution (first mode)
```

## Gift tiers (Guess the Solution mode)

| Tier | Effect |
|---|---|
| GUESS | Earn one guess token; next comment from that viewer is their answer |
| HINT | Play one step of the `Solve` timeline |
| AUTO_SOLVE | Play full `Solve` timeline, start next round |
| CUSTOM_EQUATION | Viewer's next comment becomes the new equation (parsed via `text_to_MF_Algebra`) |
| WRENCH | Replace equation with a new random one, reset timer |

Edit `gifts.py` → `GIFT_TIERS` dict with real gift names from your stream (they appear in the terminal when connected).

## MF_Algebra patterns used

```python
# Display an equation
eq_tl = Evaluate(auto_scale=2.5)
eq_tl >> equation
scene.play(Write(eq_tl.mob))

# Animate a guess (substitute + auto-evaluate)
eq_tl >>= substitute_({var: Smarten(value)}, maintain_color=True)
eq_tl.play_all(scene, wait_between=0.5)
L, R = eq_tl.get_expression(-1).children
correct = (L == R)

# Hint: one solve step
solve_tl = Solve(auto_scale=2.5)
solve_tl >>= equation.copy()
solve_tl.play_next(scene)

# Auto-solve
solve_tl.play_all(scene)
```

## Running

```bash
TIKTOK_USERNAME=@yourusername manimgl main.py TikTokGame
```

The TikTok desktop app screen-captures the ManimGL window for streaming. No FFmpeg needed.

## Adding a new game mode

1. Create `modes/your_mode.py` subclassing `GameMode` from `modes/base.py`
2. Implement `start_round`, `handle_event`, `is_round_over`, `on_timeout`
3. Swap `GuessingMode` for your mode in `scene.py`

The `GameMode` receives `scene`, `game_state`, and `event_queue`. Calling `scene.play()` from `handle_event` is safe — it blocks but keeps rendering frames internally.

## Known calibration needed

- **Gift names** in `gifts.py` are guesses; real names appear in terminal on first connection
- **`ROUND_DURATION`** in `modes/guessing.py` (currently 90s)
- **Equation pool** in `modes/guessing.py` — extend `EQUATION_POOL` with your preferred starting equations
