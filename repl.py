"""
Background-thread REPL.

Reads lines from stdin and pushes them onto a queue. The scene's main loop
drains that queue and exec's each line against itself, so you can manipulate
the live scene from the terminal without blocking the render loop.
"""

import sys
import threading


def start_repl(command_queue):
    def _loop():
        while True:
            try:
                line = input()
            except (EOFError, KeyboardInterrupt):
                return
            line = line.strip()
            if line:
                command_queue.put(line)

    t = threading.Thread(target=_loop, daemon=True)
    t.start()
    print("[repl] type Python to manipulate the scene, e.g. self.play(Write(Tex('x=5')))", file=sys.stderr)
    return t
