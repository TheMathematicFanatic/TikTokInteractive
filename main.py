"""
Entry point.

Usage:
    manimgl main.py TikTokGame -w   # opens a window (for screen capture)
    manimgl main.py TikTokGame      # same, interactive

Set TIKTOK_USERNAME below or pass it via the environment.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from manimlib import *
from scene import TikTokGameScene


class TikTokGame(TikTokGameScene):
    tiktok_username = os.environ.get("TIKTOK_USERNAME", "@TheMathematicFanatic")
