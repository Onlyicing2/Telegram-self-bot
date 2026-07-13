# LifeOS — Telegram Self-Bot & LifeOS System

Production-ready, headless Telegram userbot optimized for Render Free tier.

---

## Pre-Deploy: Generate SESSION_STRING

You must generate a Pyrogram/Telethon `StringSession` **once** on your local machine.
Run the helper script below — it handles the interactive 2FA prompt, then exits:

```bash
pip install telethon
python -c "
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
import os

api_id   = int(input('API_ID: '))
api_hash = input('API_HASH: ')

with TelegramClient(StringSession(), api_id, api_hash) as client:
    print('\\n--- SESSION_STRING ---')
    print(client.session.save())
    print('--- copy the line above ---')
"
```

Copy the output string and paste it as the `SESSION_STRING` environment variable on Render.

---

## Required Environment Variables (Render Dashboard)

| Variable | Description |
|---|---|
| `API_ID` | Telegram API ID from my.telegram.org |
| `API_HASH` | Telegram API Hash from my.telegram.org |
| `SESSION_STRING` | Generated StringSession (see above) |
| `BOT_OWNER_ID` | Your Telegram numeric user ID |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key |
| `DATABASE_URL` | PostgreSQL connection string (backup) |
| `TZ` | Timezone — defaults to `Asia/Tehran` |

---

## Command Reference

### Utility
| Command | Description |
|---|---|
| `.ping` | Edit message to `PONG` |
| `.id` | Show Chat ID + Message ID |

### Save Engine (reply to a message)
| Command | Description |
|---|---|
| `.save f` | Forward save — metadata log, no download |
| `.save d` | Deep save — download, re-upload with rich caption |
| `.preview SV-000001` | Show stored metadata |
| `.send SV-000001` | Forward saved asset to current chat |

### Organizer
| Command | Description |
|---|---|
| `.organize list` | LifeOS data overview |
| `.organize clean` | Purge logs older than 7 days |
| `.del <n>` | Delete last n outgoing messages |
| `.del id <msgid>` | Delete all messages from msgid forward |

### Bio Engine
| Command | Description |
|---|---|
| `.bio help` | Token reference |
| `.bio template <tpl>` | Set bio template (`{time}`, `{mood}`, `{text}`) |
| `.bio text <text>` | Set {text} token |
| `.bio mood <mood>` | Set {mood} token |
| `.bio on` | Start Tehran-synchronized cron |
| `.bio off` | Stop cron |
| `.bio show` | Inspect current state |

---

## Architecture

```
backend/
├── main.py          # asyncio.gather(telethon, uvicorn)
├── config.py        # env validation — hard exit on missing vars
├── bot/
│   ├── client.py    # StringSession, connect(), is_user_authorized()
│   ├── router.py    # registers all handlers
│   └── handlers/
│       ├── guard.py     # owner-only permission layer
│       ├── misc.py      # .ping, .id
│       ├── save.py      # .save f / .save d
│       ├── retrieve.py  # .preview, .send
│       ├── delete.py    # .del
│       ├── organize.py  # .organize
│       └── bio.py       # .bio
├── bio/
│   └── engine.py    # cron loop (exact minute sync, dedup)
├── db/
│   └── client.py    # supabase service-role singleton
└── web/
    └── app.py       # FastAPI + static serving

src/                 # React dashboard (dark Material 3)
├── App.tsx
├── components/
│   ├── SavedItems.tsx
│   ├── BioStatus.tsx
│   └── LogViewer.tsx
└── lib/
    └── api.ts       # typed fetch wrappers
```

## Security

- All credentials read exclusively from `os.getenv` — nothing hardcoded.
- Owner-only command gate: all other users are silently ignored.
- Session string never touches the filesystem on Render.
