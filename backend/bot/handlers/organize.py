"""
.organize list   — Structured overview of LifeOS data (saves, logs, bio).
.organize clean  — Purge transient bot_logs older than 7 days.
"""
import logging
from telethon import events
from backend.bot.handlers.guard import is_owner
from backend.db.client import get_db

logger = logging.getLogger(__name__)


def register(client, owner_id: int):

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.organize\s+(list|clean)$"))
    async def organize(event):
        if not is_owner(event, owner_id):
            return

        action = event.pattern_match.group(1)
        db = get_db()

        if action == "list":
            try:
                saves_res = db.table("saved_items").select("id", count="exact").eq("owner_id", owner_id).execute()
                fwd_res = db.table("saved_items").select("id", count="exact").eq("owner_id", owner_id).eq("save_type", "forward").execute()
                deep_res = db.table("saved_items").select("id", count="exact").eq("owner_id", owner_id).eq("save_type", "deep").execute()
                logs_res = db.table("bot_logs").select("id", count="exact").eq("owner_id", owner_id).execute()
                bio_res = db.table("bio_state").select("*").eq("owner_id", owner_id).maybeSingle().execute()
                bio = bio_res.data

                bio_status = "OFF"
                bio_template = "—"
                if bio:
                    bio_status = "ON" if bio.get("is_active") else "OFF"
                    bio_template = bio.get("template", "—")

                lines = [
                    "**LifeOS Status**\n",
                    f"📦 **Saves**",
                    f"  Total: `{saves_res.count or 0}`",
                    f"  Forward: `{fwd_res.count or 0}`",
                    f"  Deep: `{deep_res.count or 0}`\n",
                    f"📋 **Logs**",
                    f"  Entries: `{logs_res.count or 0}`\n",
                    f"🧬 **Bio Engine**",
                    f"  Status: `{bio_status}`",
                    f"  Template: `{bio_template}`",
                ]
                await event.edit("\n".join(lines))
            except Exception as exc:
                logger.error("organize list failed: %s", exc)
                await event.edit(f"❌ Error: {exc}")

        elif action == "clean":
            try:
                from datetime import datetime, timedelta, timezone
                cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
                result = db.table("bot_logs").delete().eq("owner_id", owner_id).lt("created_at", cutoff).execute()
                deleted = len(result.data) if result.data else 0
                await event.edit(f"🧹 Cleaned `{deleted}` log entries older than 7 days.")
            except Exception as exc:
                logger.error("organize clean failed: %s", exc)
                await event.edit(f"❌ Error: {exc}")
