from enum import Enum, auto
from events import GiftEvent


class GiftTier(Enum):
    GUESS = auto()            # earn the right to submit a guess
    HINT = auto()             # reveal one solve step
    AUTO_SOLVE = auto()       # solve the equation in full
    CUSTOM_EQUATION = auto()  # submit a new equation for everyone
    WRENCH = auto()           # throw a wrench into the current equation


# Map gift name (as reported by TikTok) to tier.
# Edit these to match the actual gift names you see on your stream.
GIFT_TIERS: dict[str, GiftTier] = {
    # guess tier (cheap)
    "Rose": GiftTier.GUESS,
    "TikTok": GiftTier.GUESS,
    "Heart Me": GiftTier.GUESS,
    "GG": GiftTier.GUESS,
    # hint tier (medium)
    "Finger Heart": GiftTier.HINT,
    "Sunglasses": GiftTier.HINT,
    "Hand Heart": GiftTier.HINT,
    # auto-solve tier (expensive)
    "Galaxy": GiftTier.AUTO_SOLVE,
    "Lion": GiftTier.AUTO_SOLVE,
    "Falcon": GiftTier.AUTO_SOLVE,
    # custom equation tier (very expensive)
    "Universe": GiftTier.CUSTOM_EQUATION,
    "TikTok Universe": GiftTier.CUSTOM_EQUATION,
    # wrench tier (any price — it's a chaos gift)
    "Bomb": GiftTier.WRENCH,
    "Dagger": GiftTier.WRENCH,
    "Confetti": GiftTier.WRENCH,
}

# Fallback: classify by diamond value if gift name isn't in the map.
_DIAMOND_FALLBACK: list[tuple[int, GiftTier]] = [
    (500, GiftTier.CUSTOM_EQUATION),
    (100, GiftTier.AUTO_SOLVE),
    (20,  GiftTier.HINT),
    (1,   GiftTier.GUESS),
]


def classify_gift(event: GiftEvent) -> GiftTier:
    if event.gift_name in GIFT_TIERS:
        return GIFT_TIERS[event.gift_name]
    for min_diamonds, tier in _DIAMOND_FALLBACK:
        if event.diamonds >= min_diamonds:
            return tier
    return GiftTier.GUESS
