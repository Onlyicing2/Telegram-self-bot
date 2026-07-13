"""
LifeOS — deterministic entry point.

Startup phases (strict sequential):
  1. Config validation (hard-exit on missing vars)
  2. Database connection warm-up
  3. Telethon client — connect + authorize
  4. Command handler registration (exactly once)
  5. Bio cron resume (if persisted active in DB)
  6. Uvicorn web server (background task)

Shutdown sequence on SIGTERM / SIGINT:
  A. Bio cron cancelled
  B. Uvicorn signalled to exit
  C. All remaining asyncio tasks cancelled + awaited (zero orphans)
  D. Telethon disconnected cleanly
"""
import asyncio
import logging
import signal
import sys

import uvicorn

import backend.config as cfg_module
from backend.bio import engine as bio_engine
from backend.bot.client import build_client
from backend.bot.router import register_all
from backend.db.client import get_db
from backend.web.app import app as web_app

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logging.getLogger("backend").setLevel(logging.INFO)
logging.getLogger("telethon").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Held so the shutdown sequence can signal Uvicorn directly.
_uvicorn_server: uvicorn.Server | None = None


async def _run_web(port: int) -> None:
    global _uvicorn_server
    config = uvicorn.Config(
        web_app,
        host="0.0.0.0",
        port=port,
        log_level="warning",
        access_log=False,
    )
    _uvicorn_server = uvicorn.Server(config)
    await _uvicorn_server.serve()


async def main() -> None:
    # ── Phase 0: Config ───────────────────────────────────────────────────
    cfg = cfg_module.load()

    # One-shot shutdown event; set by OS signals or Telethon disconnect.
    shutdown: asyncio.Event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, shutdown.set)
        except NotImplementedError:
            # Windows — signals not supported on event loop; Ctrl-C still works.
            pass

    # ── Phase 1: Database warm-up ─────────────────────────────────────────
    logger.info("[1/5] Database warm-up")
    try:
        get_db().table("bot_logs").select("id").limit(1).execute()
        logger.info("[1/5] Database OK")
    except Exception as exc:
        logger.warning("[1/5] Database warm-up failed (%s) — continuing", exc)

    # ── Phase 2: Telethon client ──────────────────────────────────────────
    logger.info("[2/5] Connecting Telethon")
    client = await build_client(cfg["API_ID"], cfg["API_HASH"], cfg["SESSION_STRING"])

    # ── Phase 3: Register command handlers (exactly once) ─────────────────
    logger.info("[3/5] Registering command handlers")
    register_all(client, cfg["OWNER_ID"], cfg["TZ"])

    # ── Phase 4: Resume bio cron if it was active before last restart ─────
    logger.info("[4/5] Bio cron resume check")
    try:
        result = (
            get_db()
            .table("bio_state")
            .select("is_active")
            .eq("owner_id", cfg["OWNER_ID"])
            .maybeSingle()
            .execute()
        )
        if result.data and result.data.get("is_active"):
            bio_engine.start_cron(client, cfg["OWNER_ID"], cfg["TZ"])
            logger.info("[4/5] Bio cron resumed")
    except Exception as exc:
        logger.warning("[4/5] Bio cron resume check failed: %s", exc)

    # ── Phase 5: Web server (background, non-blocking) ────────────────────
    logger.info("[5/5] Starting web server on port %s", cfg["PORT"])
    web_task = asyncio.create_task(_run_web(cfg["PORT"]), name="lifeos-web")

    # ── Main: run until Telethon disconnects OR shutdown signal ───────────
    logger.info("LifeOS online.")
    tg_task = asyncio.create_task(
        client.run_until_disconnected(), name="lifeos-tg"
    )
    shutdown_task = asyncio.create_task(shutdown.wait(), name="lifeos-shutdown")

    await asyncio.wait(
        {tg_task, shutdown_task},
        return_when=asyncio.FIRST_COMPLETED,
    )

    # ── Shutdown A: bio cron ──────────────────────────────────────────────
    logger.info("Shutdown: stopping bio cron")
    bio_engine.stop_cron()

    # ── Shutdown B: web server ────────────────────────────────────────────
    logger.info("Shutdown: signalling web server")
    if _uvicorn_server is not None:
        _uvicorn_server.should_exit = True

    # ── Shutdown C: all remaining tasks ───────────────────────────────────
    logger.info("Shutdown: cancelling all tasks")
    pending = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in pending:
        task.cancel()
    await asyncio.gather(*pending, return_exceptions=True)

    # ── Shutdown D: Telethon ──────────────────────────────────────────────
    logger.info("Shutdown: disconnecting Telethon")
    try:
        await client.disconnect()
    except Exception as exc:
        logger.warning("Telethon disconnect: %s", exc)

    logger.info("LifeOS stopped cleanly.")


if __name__ == "__main__":
    asyncio.run(main())
