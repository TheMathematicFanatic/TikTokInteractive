"""
TikTokLive background listener.

Runs an asyncio event loop in a daemon thread. Only ever touches the
shared queue — all other state lives on the main (ManimGL) thread.
"""

import asyncio
import queue
import threading
import time

from events import CommentEvent, GiftEvent


def start_listener(username: str, event_queue: queue.Queue, verbose: bool = True) -> threading.Thread:
    def run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            from TikTokLive import TikTokLiveClient
            from TikTokLive.events import (
                CommentEvent as TKComment,
                GiftEvent as TKGift,
                ConnectEvent,
                DisconnectEvent,
            )
        except ImportError:
            print("[listener] TikTokLive not installed — run: pip install TikTokLive")
            return

        client = TikTokLiveClient(unique_id=username)

        @client.on(ConnectEvent)
        async def on_connect(_event):
            if verbose:
                print(f"[TikTok] Connected to @{username}")

        @client.on(DisconnectEvent)
        async def on_disconnect(_event):
            if verbose:
                print("[TikTok] Disconnected")

        @client.on(TKComment)
        async def on_comment(event: TKComment):
            event_queue.put(CommentEvent(
                user=event.user.nickname,
                text=event.comment,
                timestamp=time.time(),
            ))

        @client.on(TKGift)
        async def on_gift(event: TKGift):
            # Only process at the end of a repeat streak to avoid double-counting.
            if hasattr(event, "repeat_end") and not event.repeat_end:
                return
            event_queue.put(GiftEvent(
                user=event.user.nickname,
                gift_name=event.gift.name,
                gift_id=event.gift.id,
                diamonds=event.gift.diamond_count,
                repeat_count=getattr(event, "repeat_count", 1),
                timestamp=time.time(),
            ))

        try:
            client.run()
        except Exception as exc:
            if verbose:
                print(f"[TikTok] Listener stopped: {exc}")

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return thread
