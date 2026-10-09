import logging
import time
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse

from app import config
from app.forge.config import forge_config_from_environment
from app.forge.observability.service import observability_from_config
from app.forge.providers.registry import providers_from_config
from app.forge.service.container import ForgeServiceContainer
from app.forge.service.lifecycle import ForgeLifecycle
from app.forge.service.routes import create_forge_router
from app.state_engine import get_engine, reset_engine
from app.trade_log import get_recent_signals, log_signal
from app.validator import validate

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

_start_time = time.time()

app = FastAPI(title="CEREBUS Signal Guard", version="1.0.0")


def _build_forge_container() -> ForgeServiceContainer:
    """FORGE composition root for the existing application.

    This keeps FORGE isolated from Signal Guard domain behavior while reusing
    the single existing FastAPI application.

    II.5: configuration selects the provider adapters here (Ch II.5.6) —
    deterministic in-process fakes until Book IV/VI register concrete
    builders. Unknown provider names fail closed at startup.

    II.6: the observability seam is wired from config when enabled
    (in-process sinks only, no vendor); disabled leaves it unwired and
    readiness discloses NOT_CONFIGURED honestly.
    """
    forge_config = forge_config_from_environment()
    return ForgeServiceContainer(
        config=forge_config,
        providers=providers_from_config(forge_config),
        observability=(
            observability_from_config(forge_config)
            if forge_config.observability_enabled
            else None
        ),
    )


def _attach_forge_router() -> None:
    """Explicitly attach FORGE routes so integration is intentional."""
    container = _build_forge_container()
    lifecycle = ForgeLifecycle(container=container)
    forge_router = create_forge_router(
        config=container.config,
        container=container,
    )
    app.include_router(forge_router)
    # Sub-router on_event handlers never fire once included, so lifecycle is
    # appended to the application's own startup/shutdown sequence. This does
    # not alter the existing Signal Guard startup handler below.
    app.router.on_startup.append(lifecycle.startup)
    app.router.on_shutdown.append(lifecycle.shutdown)
    logger.info(
        "FORGE router attached: prefix=/forge/v1 env=%s",
        container.config.environment,
    )


# Attach FORGE service skeleton at application startup.
_attach_forge_router()


@app.on_event("startup")
async def startup():
    Path("data").mkdir(parents=True, exist_ok=True)
    Path("logs/screenshots").mkdir(parents=True, exist_ok=True)
    get_engine()
    logger.info("CEREBUS Signal Guard started. Position: %s", get_engine().get_position())


# ---------------------------------------------------------------------------
# POST /webhook — TradingView alert receiver
# ---------------------------------------------------------------------------

@app.post("/webhook")
async def webhook(request: Request):
    # Webhook secret auth (optional — TV doesn't support custom headers natively,
    # but you can embed the secret in the JSON payload or URL param)
    secret = config.WEBHOOK_SECRET
    if secret:
        incoming = request.headers.get("X-TradingView-Secret", "")
        if incoming != secret:
            raise HTTPException(status_code=401, detail="invalid_secret")

    try:
        signal = await request.json()
    except Exception:
        raw = await request.body()
        logger.error("Failed to parse webhook body: %s", raw)
        raise HTTPException(status_code=422, detail="invalid_json")

    logger.info(
        "Webhook received: signal_id=%s action=%s",
        signal.get("signal_id"),
        signal.get("action"),
    )

    result = validate(signal)
    log_signal(signal, result)

    logger.info(
        "Validation result: signal_id=%s result=%s reason=%s",
        result.signal_id,
        result.result,
        result.reason,
    )

    return result.to_dict()


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    uptime = int(time.time() - _start_time)
    try:
        position = get_engine().get_position()
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "error": str(exc)},
        )
    return {
        "status": "ok",
        "position": position,
        "uptime_seconds": uptime,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# GET /state
# ---------------------------------------------------------------------------

@app.get("/state")
async def state():
    engine = get_engine()
    return {
        "position": engine.get_position(),
        "history": engine.get_history(n=20),
    }


# ---------------------------------------------------------------------------
# POST /reconcile — force position check (stub in Phase 1)
# ---------------------------------------------------------------------------

@app.post("/reconcile")
async def reconcile():
    engine = get_engine()
    position = engine.get_position()
    logger.info("Reconcile requested. Current position: %s", position)
    # Phase 3: compare with actual broker position and correct if needed
    return {
        "status": "ok",
        "position": position,
        "note": "Phase 1 — reconcile is a no-op. Phase 3 will check broker.",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# GET /logs
# ---------------------------------------------------------------------------

@app.get("/logs")
async def logs(n: int = 50):
    rows = get_recent_signals(n)
    return {"count": len(rows), "signals": rows}


# ---------------------------------------------------------------------------
# GET /screenshot
# ---------------------------------------------------------------------------

@app.get("/screenshot")
async def screenshot():
    screenshots_dir = Path("logs/screenshots")
    if not screenshots_dir.exists():
        return {"last_screenshot": None}
    files = sorted(screenshots_dir.iterdir(), key=lambda f: f.stat().st_mtime, reverse=True)
    if not files:
        return {"last_screenshot": None}
    latest = files[0]
    return {
        "last_screenshot": str(latest),
        "filename": latest.name,
        "modified": datetime.fromtimestamp(
            latest.stat().st_mtime, tz=timezone.utc
        ).isoformat(),
    }
