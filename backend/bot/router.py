"""
Handler registration — wires all command handlers onto the Telethon client.
"""
from backend.bot.handlers import misc, save, retrieve, delete, organize, bio


def register_all(client, owner_id: int, tz_str: str):
    misc.register(client, owner_id)
    save.register(client, owner_id, tz_str)
    retrieve.register(client, owner_id)
    delete.register(client, owner_id)
    organize.register(client, owner_id)
    bio.register(client, owner_id, tz_str)
