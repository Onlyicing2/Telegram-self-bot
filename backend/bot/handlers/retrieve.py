"""
.preview <id>  — Show stored metadata for a saved item.
.send <id>     — Forward the saved asset into the current chat.
"""
import logging
from telethon import events
from backend.bot.handlers.guard import is_owner
from backend.db.client import get_db, log

logger = logging.getLogger(__name__)


def _format_preview(row: dict) -> str:
    size_str = f"{row['file_size'] / 1024:.1f} KB" if row.get("file_size") else "—"
    tags = " ".join(row.get("tags") or [])
    return (
        f"**Save Code:** `{row['save_code']}`\n"
        f"**Type:** {row.get('save_type', '—').title()}\n"
        f"**Media:** {row.get('media_type', '—')}\n"
        f"**MIME:** `{row.get('mime_type') or '—'}`\n"
        f"**Size:** {size_str}\n"
        f"**Sender:** {row.get('sender_name') or '—'}\n"
        f"**Origin Chat:** `{row.get('origin_chat_id')}`\n"
        f"**Origin Msg:** `{row.get('origin_msg_id')}`\n"
        f"**Saved At:** {str(row.get('created_at', '—'))[:19]}\n"
        f"**Tags:** {tags or '—'}"
    )


def register(client, owner_id: int):

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.preview\s+(\S+)$"))
    async def preview(event):
        if not is_owner(event, owner_id):
            return
        save_code = event.pattern_match.group(1).upper()
        db = get_db()
        try:
            result = db.table("saved_items").select("*").eq("save_code", save_code).maybeSingle().execute()
            row = result.data
        except Exception as exc:
            logger.error("preview db error: %s", exc)
            await event.edit(f"❌ DB error: {exc}")
            return
        if not row:
            await event.edit(f"❌ No item found for `{save_code}`")
            return
        await event.edit(_format_preview(row))

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.send\s+(\S+)$"))
    async def send_cmd(event):
        if not is_owner(event, owner_id):
            return
        save_code = event.pattern_match.group(1).upper()
        db = get_db()
        try:
            result = db.table("saved_items").select("*").eq("save_code", save_code).maybeSingle().execute()
            row = result.data
        except Exception as exc:
            logger.error("send db error: %s", exc)
            await event.edit(f"❌ DB error: {exc}")
            return
        if not row:
            await event.edit(f"❌ No item found for `{save_code}`")
            return

        saved_chat_id = row.get("saved_chat_id")
        saved_msg_id = row.get("saved_msg_id")
        if not saved_chat_id or not saved_msg_id:
            await event.edit("❌ Saved location data is missing for this entry.")
            return

        target_chat = event.chat_id
        try:
            await client.forward_messages(target_chat, saved_msg_id, saved_chat_id)
            await event.delete()
        except Exception as exc:
            logger.error("send forward failed: %s", exc)
            await event.edit(f"❌ Forward failed: {exc}")
            return

        await log(owner_id, "INFO", f"Sent {save_code} to {target_chat}", {
            "save_code": save_code,
            "target_chat": target_chat,
        })
