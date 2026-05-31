from abc import ABC, abstractmethod
from events import TikTokEvent


class GameMode(ABC):
    """
    A self-contained game mode.

    The scene calls start_round() to begin and handle_event() for every
    event that arrives from the queue.  All calls happen on the main
    (ManimGL) thread, so it is safe to call scene.play() etc. directly.
    """

    def __init__(self, scene, game_state, event_queue):
        self.scene = scene
        self.state = game_state
        self.queue = event_queue

    # ------------------------------------------------------------------
    # Subclasses must implement

    @abstractmethod
    def start_round(self, equation=None):
        """Set up and display the first/next round."""
        ...

    @abstractmethod
    def handle_event(self, event: TikTokEvent):
        """React to a comment or gift.  May call self.scene.play()."""
        ...

    @abstractmethod
    def is_round_over(self) -> bool:
        """Return True when the current round has ended."""
        ...

    @abstractmethod
    def on_timeout(self):
        """Called by the scene when is_round_over() fires due to time."""
        ...
