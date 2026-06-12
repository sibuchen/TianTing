import json
import logging

import lark_oapi as lark
from lark_oapi.api.im.v1 import *
from lark_oapi.api.contact.v3 import *

from app.im import IMClient
from app.config import settings

logger = logging.getLogger(__name__)


class FeishuClient(IMClient):

    def __init__(self) -> None:
        self._client = lark.Client.builder() \
            .app_id(settings.feishu_app_id) \
            .app_secret(settings.feishu_app_secret) \
            .build()

    async def send_message(self, user_id: str, text: str) -> bool:
        try:
            request = CreateMessageRequest.builder() \
                .receive_id_type("open_id") \
                .request_body(
                    CreateMessageRequestBody.builder()
                    .receive_id(user_id)
                    .msg_type("text")
                    .content(json.dumps({"text": text}))
                    .build()
                ) \
                .build()
            resp = await self._client.im.v1.message.acreate(request)
            if not resp.success():
                logger.error(f"Feishu send_message failed: {resp.code} {resp.msg}")
                return False
            return True
        except Exception as e:
            logger.error(f"Feishu send_message error: {e}")
            return False

    async def reply_message(self, message_id: str, text: str) -> bool:
        try:
            request = ReplyMessageRequest.builder() \
                .message_id(message_id) \
                .request_body(
                    ReplyMessageRequestBody.builder()
                    .msg_type("text")
                    .content(json.dumps({"text": text}))
                    .build()
                ) \
                .build()
            resp = await self._client.im.v1.message.areply(request)
            if not resp.success():
                logger.error(f"Feishu reply_message failed: {resp.code} {resp.msg}")
                return False
            return True
        except Exception as e:
            logger.error(f"Feishu reply_message error: {e}")
            return False

    async def get_user_name(self, user_id: str) -> str | None:
        try:
            request = GetUserRequest.builder() \
                .user_id(user_id) \
                .user_id_type("open_id") \
                .build()
            resp = await self._client.contact.v3.user.aget(request)
            if resp.success() and resp.data and resp.data.user:
                return resp.data.user.name
            return None
        except Exception as e:
            logger.error(f"Feishu get_user_name error: {e}")
            return None


_feishu_client: FeishuClient | None = None


def get_feishu_client() -> FeishuClient:
    global _feishu_client
    if _feishu_client is None:
        _feishu_client = FeishuClient()
    return _feishu_client
