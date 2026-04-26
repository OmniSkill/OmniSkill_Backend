"""WebSocket endpoint for streaming profile generation events."""

import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

router = APIRouter()


@router.websocket("/ws/profile/{profile_id}")
async def profile_events_ws(websocket: WebSocket, profile_id: str) -> None:
    """Stream node completion events to the frontend during profile generation."""
    await websocket.accept()
    logger.info("WebSocket connected for profile {}", profile_id[:8])

    redis = getattr(websocket.app.state, "redis", None)
    if redis is None:
        await websocket.send_json({"event": "error", "detail": "Redis not available"})
        await websocket.close()
        return

    pubsub = redis.pubsub()
    channel = f"profile_events:{profile_id}"
    await pubsub.subscribe(channel)

    try:
        while True:
            message = await asyncio.wait_for(
                pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0),
                timeout=300,
            )
            if message and message["type"] == "message":
                data = message["data"]
                if isinstance(data, bytes):
                    data = data.decode()
                event = json.loads(data)
                await websocket.send_json(event)

                if event.get("event") in ("completed", "failed"):
                    break

    except (TimeoutError, WebSocketDisconnect):
        logger.info("WebSocket disconnected for profile {}", profile_id[:8])
    except Exception as exc:
        logger.error("WebSocket error for profile {}: {}", profile_id[:8], exc)
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.aclose()
