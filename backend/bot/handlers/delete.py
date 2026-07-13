"""
.del <n>         — Delete the last n outgoing messages in this chat.
.del id <msgid>  — Delete all messages from <msgid> forward in this chat.

Edit-first policy: error feedback edits the trigger message.
Successful deletion silently removes all targeted messages (including the command).
"""
import logging
from telethon import events
from backend.bot.handlers.guard import is_owner

logger = logging.getLogger(__name__)

_BATCH = 100


def register(client, owner_id: int):

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.del(?:\s+(.+))?$"))
    async def del_cmd(event):
        if not is_owner(event, owner_id):
            return

        arg = (event.pattern_match.group(1) or "").strip()

        if arg.lower().startswith("id "):
            rest = arg[3:].strip()
            if not rest.isdigit():
                await event.edit("⚠️ Usage: `.del id <msgid>`")
                return
            start_id = int(rest)
            await event.delete()
            try:
                msg_ids = []
                async for msg in client.iter_messages(event.chat_id, min_id=start_id - 1):
                    msg_ids.append(msg.id)
                    if len(msg_ids) >= _BATCH:
                        await client.delete_messages(event.chat_id, msg_ids)
                        msg_ids = []
                if msg_ids:
                    await client.delete_messages(event.chat_id, msg_ids)
            except Exception as exc:
                logger.error("del id failed: %s", exc)

        elif arg.isdigit():
            n = int(arg)
            if n < 1 or n > 500:
                await event.edit("⚠️ n must be between 1 and 500.")
                return
            await event.delete()
            try:
                msg_ids = []
                async for msg in client.iter_messages(event.chat_id, limit=n + 5, from_user="me"):
                    msg_ids.append(msg.id)
                    if len(msg_ids) >= n:
                        break
                if msg_ids:
                    await client.delete_messages(event.chat_id, msg_ids[:n])
            except Exception as exc:
                logger.error("del n failed: %s", exc)

        else:
            await event.edit("⚠️ Usage: `.del <n>` or `.del id <msgid>`")
