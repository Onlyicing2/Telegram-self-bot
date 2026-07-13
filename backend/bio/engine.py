"""
Bio Engine — Tehran-synchronized Telegram bio cron.

Guarantees:
- Fires exactly at xx:xx:00 (Tehran time) by sleeping
  (60 - second - microsecond/1e6) seconds to the next minute boundary.
- Deduplicates: skips the Telegram API call when the rendered string
  has not changed since the last confirmed update.
- FloodWaitError is caught and slept precisely; all other errors are
  logged as warnings so the loop never terminates on Telegram throttles.
"""
import asyncio
import logging
from datetime import datetime

import pytz
from telethon.errors import FloodWaitError

from backend.db.client import get_db

logger = logging.getLogger(__name__)

_task: asyncio.Task | None = None


def render_bio(template: str, mood: str, text: str, tz_str: str) -> str:
    tz = pytz.timezone(tz_str)
    now = datetime.now(tz)
    return (
        template
        .replace("{time}", now.strftime("%H:%M"))
        .replace("{mood}", mood)
        .replace("{text}", text)
    )


def _seconds_to_next_minute(tz: pytz.BaseTzInfo) -> float:
    """Return the precise fractional seconds until the next xx:xx:00.000."""
    now = datetime.now(tz)
    wait = 60.0 - now.second - now.microsecond / 1_000_000
    if wait <= 0:
        wait += 60.0
    return wait


async def _cron_loop(client, owner_id: int, tz_str: str) -> None:
    """Runs indefinitely; the only exit is asyncio.CancelledError (bio off)."""
    tz = pytz.timezone(tz_str)
    logger.info("Bio cron started (tz=%s)", tz_str)

    while True:
        # ── Phase 1: align to the next exact minute boundary ──────────────
        await asyncio.sleep(_seconds_to_next_minute(tz))

        # ── Phase 2: read state ───────────────────────────────────────────
        try:
            db = get_db()
            result = (
                db.table("bio_state")
                .select("*")
                .eq("owner_id", owner_id)
                .maybeSingle()
                .execute()
            )
            state = result.data

            if not state or not state.get("is_active"):
                logger.info("Bio cron: is_active=False — stopping loop.")
                return

            new_bio = render_bio(
                state.get("template", "🕒 {time} | 💭 {mood}"),
                state.get("mood", "😊"),
                state.get("custom_text", ""),
                tz_str,
            )

            # ── Phase 3: dedup gate — zero redundant API calls ────────────
            if new_bio == state.get("last_bio", ""):
                continue

            # ── Phase 4: Telegram API call (isolated) ─────────────────────
            try:
                await client.edit_profile(about=new_bio)
            except FloodWaitError as fwe:
                # Honour Telegram's mandated wait; resume after the hold-off
                logger.warning("Bio FloodWait %ds — sleeping.", fwe.seconds)
                await asyncio.sleep(fwe.seconds + 1)
                continue
            except asyncio.CancelledError:
                raise
            except Exception as api_exc:
                logger.warning("Bio API error (retrying next minute): %s", api_exc)
                continue

            # ── Phase 5: persist the new bio so next tick can dedup ───────
            db.table("bio_state").update({
                "last_bio": new_bio,
                "updated_at": datetime.now(tz).isoformat(),
            }).eq("owner_id", owner_id).execute()

        except asyncio.CancelledError:
            logger.info("Bio cron cancelled.")
            raise
        except Exception as exc:
            # DB error or unexpected — log, never crash the loop
            logger.warning("Bio cron tick error (will retry next minute): %s", exc)


def start_cron(client, owner_id: int, tz_str: str) -> None:
    global _task
    if _task and not _task.done():
        return
    _task = asyncio.create_task(_cron_loop(client, owner_id, tz_str))


def stop_cron() -> None:
    global _task
    if _task and not _task.done():
        _task.cancel()
    _task = None


def is_running() -> bool:
    return bool(_task and not _task.done())
