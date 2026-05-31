import time
from dataclasses import dataclass, field


@dataclass
class TikTokEvent:
    user: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class CommentEvent(TikTokEvent):
    text: str = ""


@dataclass
class GiftEvent(TikTokEvent):
    gift_name: str = ""
    gift_id: int = 0
    diamonds: int = 0
    repeat_count: int = 1
