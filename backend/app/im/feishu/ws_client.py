import json
import logging
import asyncio
import threading
from dataclasses import dataclass

import lark_oapi as lark
from lark_oapi.api.im.v1 import P2ImMessageReceiveV1
from lark_oapi.ws import client as _ws_client_mod

from app.config import settings

logger = logging.getLogger(__name__)

_ws_client: lark.ws.Client | None = None
_ws_thread: threading.Thread | None = None
_main_loop: asyncio.AbstractEventLoop | None = None
_message_queue: asyncio.Queue | None = None
_consumer_task: asyncio.Task | None = None


@dataclass
class QueuedMessage:
    open_id: str
    chat_id: str
    message_text: str
    message_id: str | None


def _on_message_receive(data: P2ImMessageReceiveV1) -> None:
    try:
        event = data.event
        if not event or not event.message:
            return

        message = event.message
        sender = event.sender
        if not sender or not sender.sender_id:
            return

        open_id = sender.sender_id.open_id or ""
        chat_id = message.chat_id or ""
        message_id = message.message_id or ""
        msg_type = message.message_type or ""

        content_str = message.content or "{}"
        try:
            content_data = json.loads(content_str)
        except json.JSONDecodeError:
            content_data = {}

        if msg_type == "text":
            text = content_data.get("text", "")
        else:
            text = content_str

        if not text.strip():
            return

        queued = QueuedMessage(
            open_id=open_id,
            chat_id=chat_id,
            message_text=text,
            message_id=message_id,
        )

        if _main_loop is None or _message_queue is None:
            logger.warning("Message queue not initialized, dropping message")
            return

        _main_loop.call_soon_threadsafe(_message_queue.put_nowait, queued)

    except Exception as e:
        logger.error(f"Feishu WS message handler error: {e}")


async def _process_message(
    open_id: str, chat_id: str, message_text: str, message_id: str | None
) -> None:
    from app.core.database import get_db_context
    from app.im.feishu.handler import handle_feishu_message

    logger.debug(f"[_process_message] Getting db session for msg: {message_text[:50]}")
    try:
        async with get_db_context() as db_session:
            logger.debug(f"[_process_message] Got db session, calling handle_feishu_message...")
            await handle_feishu_message(
                open_id=open_id,
                chat_id=chat_id,
                message_text=message_text,
                message_id=message_id,
                db=db_session,
            )
            logger.debug(f"[_process_message] handle_feishu_message completed")
    except Exception as e:
        logger.error(f"Feishu WS handler error: {e}", exc_info=True)


async def _message_consumer() -> None:
    """消息队列消费者，在主事件循环中异步处理消息"""
    global _message_queue

    if _message_queue is None:
        return

    while True:
        try:
            msg = await _message_queue.get()
            if msg is None:
                # Poison pill: stop consumer
                _message_queue.task_done()
                break
            await _process_message(msg.open_id, msg.chat_id, msg.message_text, msg.message_id)
            _message_queue.task_done()
        except asyncio.CancelledError:
            logger.info("Feishu message consumer task cancelled")
            break
        except Exception as e:
            logger.error(f"Feishu message consumer error: {e}")
            continue


def start_ws_client() -> None:
    global _ws_client, _ws_thread, _main_loop, _message_queue, _consumer_task

    _main_loop = asyncio.get_event_loop()

    if not settings.feishu_enabled:
        logger.info("Feishu integration is disabled, WS client not started")
        return

    if settings.feishu_event_mode != "websocket":
        logger.info("Feishu event mode is webhook, WS client not started")
        return

    # 创建消息队列并启动消费者任务（在主事件循环中）
    _message_queue = asyncio.Queue(maxsize=100)
    _consumer_task = _main_loop.create_task(_message_consumer())

    event_handler = (
        lark.EventDispatcherHandler.builder("", "")
        .register_p2_im_message_receive_v1(_on_message_receive)
        .build()
    )

    _ws_client = lark.ws.Client(
        settings.feishu_app_id,
        settings.feishu_app_secret,
        event_handler=event_handler,
        log_level=lark.LogLevel.DEBUG if settings.debug else lark.LogLevel.INFO,
    )

    def _run_ws():
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        _ws_client_mod.loop = new_loop
        try:
            logger.info("Starting Feishu WebSocket client...")
            _ws_client.start()
        except Exception as e:
            logger.error(f"Feishu WS client error: {e}")
        finally:
            new_loop.close()

    _ws_thread = threading.Thread(target=_run_ws, daemon=True, name="feishu-ws")
    _ws_thread.start()
    logger.info("Feishu WebSocket client thread started, message consumer running in main loop")


def stop_ws_client() -> None:
    global _ws_client, _ws_thread, _message_queue, _consumer_task
    logger.info("Stopping Feishu WebSocket client...")

    # 停止消息消费者
    if _main_loop is not None and _message_queue is not None and not _message_queue.empty():
        # 放入 poison pill 通知消费者退出
        _main_loop.call_soon_threadsafe(_message_queue.put_nowait, None)

    if _consumer_task is not None and not _consumer_task.done():
        if _main_loop is not None:
            _main_loop.call_soon_threadsafe(_consumer_task.cancel)
        _consumer_task = None

    if _message_queue is not None:
        _message_queue = None

    _ws_client = None
    _ws_thread = None
