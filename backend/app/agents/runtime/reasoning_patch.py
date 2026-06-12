from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

_PATCH_APPLIED = False


def apply_reasoning_content_patch():
    global _PATCH_APPLIED
    if _PATCH_APPLIED:
        return

    try:
        from langchain_openai.chat_models import base as lc_base

        original_convert_from_v1 = lc_base._convert_from_v1_to_chat_completions

        def patched_convert_from_v1(message):
            if isinstance(message.content, list):
                new_content = []
                reasoning_texts = []
                for block in message.content:
                    if isinstance(block, dict):
                        block_type = block.get("type")
                        if block_type == "text":
                            new_content.append({"type": "text", "text": block["text"]})
                        elif block_type == "reasoning":
                            reasoning_texts.append(
                                block.get("text", block.get("reasoning_content", ""))
                            )
                        elif block_type == "tool_call":
                            pass
                        else:
                            new_content.append(block)
                    else:
                        new_content.append(block)

                if reasoning_texts:
                    combined = "\n".join(reasoning_texts)
                    new_content.insert(0, {"type": "reasoning", "reasoning_content": combined})

                return message.model_copy(update={"content": new_content})

            return message

        lc_base._convert_from_v1_to_chat_completions = patched_convert_from_v1

        original_get_request_payload = lc_base.BaseChatOpenAI._get_request_payload

        def patched_get_request_payload(self, input_, *, stop=None, **kwargs):
            payload = original_get_request_payload(self, input_, stop=stop, **kwargs)

            if "thinking" not in payload:
                payload["extra_body"] = {"thinking": {"type": "disabled"}}

            messages = payload.get("messages", [])
            for msg in messages:
                if not isinstance(msg, dict):
                    continue
                if msg.get("role") != "assistant":
                    continue

                content = msg.get("content")

                if isinstance(content, list):
                    reasoning_texts = []
                    new_content = []
                    for block in content:
                        if isinstance(block, dict) and block.get("type") in ("reasoning", "thinking"):
                            reasoning_texts.append(
                                block.get("text", block.get("reasoning_content", ""))
                            )
                        else:
                            new_content.append(block)
                    if reasoning_texts:
                        msg["reasoning_content"] = "\n".join(reasoning_texts)
                        msg["content"] = new_content if new_content else ""

            return payload

        lc_base.BaseChatOpenAI._get_request_payload = patched_get_request_payload
        _PATCH_APPLIED = True
        logger.info("Applied reasoning_content monkey-patches for ChatOpenAI")
    except Exception as e:
        logger.error(f"Failed to apply reasoning_content patch: {e}")