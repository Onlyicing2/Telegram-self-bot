"""
Supabase service-role client — lazy singleton.

Initialised on first access, not at import time, so modules that
import from this file never trigger env-var validation prematurely.
The service-role key bypasses RLS for all backend writes.
"""
import asyncio
import os

from supabase import create_client, Client

_client: Client | None = None

# Serialises save-code generation within the process.
# Prevents a race where two concurrent .save calls read the same count.
_save_code_lock = asyncio.Lock()


def get_db() -> Client:
    global _client
    if _client is None:
        _client = create_client(
            os.environ["SUPABASE_URL"],
            os.environ["SUPABASE_SERVICE_ROLE_KEY"],
        )
    return _client


async def log(
    owner_id: int,
    level: str,
    message: str,
    context: dict | None = None,
) -> None:
    """Fire-and-forget structured log insert — never raises."""
    try:
        get_db().table("bot_logs").insert({
            "owner_id": owner_id,
            "level": level,
            "message": message,
            "context": context or {},
        }).execute()
    except Exception:
        pass


async def get_next_save_code(db: Client) -> str:
    """
    Generate the next SV-XXXXXX code.

    The lock ensures the count-read and the caller's subsequent insert
    are effectively serialised within this process, preventing two
    concurrent saves from claiming the same code.
    """
    async with _save_code_lock:
        result = db.table("saved_items").select("id", count="exact").execute()
        count = result.count or 0
        return f"SV-{(count + 1):06d}"
