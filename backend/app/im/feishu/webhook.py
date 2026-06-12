import json
import logging

from fastapi import APIRouter, Request, Response

from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/webhook")
async def feishu_webhook(request: Request):
    if not settings.feishu_enabled:
        return Response(content="Feishu integration is disabled", status_code=503)

    body = await request.json()

    challenge = body.get("challenge")
    token = body.get("token")
    event_type = body.get("type")
    header = body.get("header", {})
    schema_v2_event_type = header.get("event_type")

    if event_type == "url_verification":
        if token != settings.feishu_verification_token:
            return Response(content="Invalid verification token", status_code=403)
        return {"challenge": challenge}

    if schema_v2_event_type == "im.message.receive_v1":
        if not _verify_token_from_header(header):
            return Response(content="Invalid token", status_code=403)
        event = body.get("event", {})
        message = event.get("message", {})
        sender = event.get("sender", {})
        sender_id = sender.get("sender_id", {})

        open_id = sender_id.get("open_id", "")
        chat_id = message.get("chat_id", "")
        message_id = message.get("message_id", "")
        msg_type = message.get("message_type", "")

        content_str = message.get("content", "{}")
        try:
            content_data = json.loads(content_str)
        except json.JSONDecodeError:
            content_data = {}

        if msg_type == "text":
            text = content_data.get("text", "")
        else:
            text = content_str

        if not text.strip():
            return {"code": 0}

        from app.im.feishu.handler import handle_feishu_message
        from app.core.database import get_db

        async for db_session in get_db():
            try:
                await handle_feishu_message(
                    open_id=open_id,
                    chat_id=chat_id,
                    message_text=text,
                    message_id=message_id,
                    db=db_session,
                )
            except Exception as e:
                logger.error(f"Error handling feishu message: {e}")
            break

    return {"code": 0}


def _verify_token_from_header(header: dict) -> bool:
    token = header.get("token", "")
    return token == settings.feishu_verification_token
