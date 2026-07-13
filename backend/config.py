"""
Environment variable loader with hard-fail on missing required keys.
All credentials read exclusively from os.getenv — nothing hardcoded.
"""
import os
import sys

REQUIRED = [
    "API_ID",
    "API_HASH",
    "SESSION_STRING",
    "BOT_OWNER_ID",
    "SUPABASE_URL",
    "SUPABASE_SERVICE_ROLE_KEY",
]


def load() -> dict:
    missing = [k for k in REQUIRED if not os.getenv(k)]
    if missing:
        print(f"[FATAL] Missing required environment variables: {', '.join(missing)}", flush=True)
        sys.exit(1)

    return {
        "API_ID": int(os.environ["API_ID"]),
        "API_HASH": os.environ["API_HASH"],
        "SESSION_STRING": os.environ["SESSION_STRING"],
        "OWNER_ID": int(os.environ["BOT_OWNER_ID"]),
        "SUPABASE_URL": os.environ["SUPABASE_URL"],
        "SUPABASE_KEY": os.environ["SUPABASE_SERVICE_ROLE_KEY"],
        "DATABASE_URL": os.getenv("DATABASE_URL", ""),
        "TZ": os.getenv("TZ", "Asia/Tehran"),
        "PORT": int(os.getenv("PORT", "8000")),
    }
