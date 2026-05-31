"""
Entry point.

Usage:
    manimgl main.py TikTokGame -w   # opens a window (for screen capture)
    manimgl main.py TikTokGame      # same, interactive

Set TIKTOK_USERNAME below or pass it via the environment.
"""

import os

from manimlib import *
from scene import TikTokGameScene


class TikTokGame(TikTokGameScene):
    tiktok_username = os.environ.get("TIKTOK_USERNAME", "@TheMathematicFanatic")
