"""
Agent Runtime Context
统一上下文组装与工具定义
"""

import hashlib
import logging
from dataclasses import dataclass, field
from typing import Callable, TypedDict

logger = logging.getLogger(__name__)


class ToolDefinition(TypedDict, total=False):
    """统一的工具定义类型，替代裸 dict 拼装"""
    type: str                     # "function"
    function: dict                # {"name": str, "description": str, "parameters": dict}
    is_readonly: bool             # 是否只读操作（借鉴 Claude Code fail-closed 原则）
    is_destructive: bool          # 是否破坏性操作
    permission_handler: Callable[[dict, str], tuple[bool, str | None]]


@dataclass
class AgentContext:
    """Agent 上下文统一组装器

    将 System Prompt 的组装逻辑从散落的字符串拼接统一为分层构建。
    分层设计便于后续 Prompt Cache 优化（静态/动态分离）。
    """

    base_prompt: str = ""
    skill_metadata: list[str] = field(default_factory=list)
    tool_descriptions: list[str] = field(default_factory=list)
    knowledge_context: str = ""
    channel: str = "web"
    enable_cache_hints: bool = False
    _last_prompt_hash: str | None = field(default=None, init=False, repr=False)

    def build_system_prompt(self) -> str:
        """按 Base → Skills → Tools → Knowledge 层次组装 System Prompt"""
        parts: list[str] = []

        if self.base_prompt:
            if self.enable_cache_hints:
                parts.append(f"<!-- CACHE: static -->\n{self.base_prompt}")
            else:
                parts.append(self.base_prompt)

        if self.skill_metadata:
            metadata_text = "\n".join(self.skill_metadata)
            if self.enable_cache_hints:
                parts.append(f"<!-- CACHE: dynamic -->\n---\n可用技能:\n{metadata_text}")
            else:
                parts.append(f"---\n可用技能:\n{metadata_text}")

        if self.tool_descriptions:
            tool_text = "\n".join(self.tool_descriptions)
            if self.enable_cache_hints:
                parts.append(f"<!-- CACHE: dynamic -->\n---\n可用工具描述:\n{tool_text}")
            else:
                parts.append(f"---\n可用工具描述:\n{tool_text}")

        if self.knowledge_context:
            if self.enable_cache_hints:
                parts.append(f"<!-- CACHE: dynamic -->\n---\n知识库上下文:\n{self.knowledge_context}")
            else:
                parts.append(f"---\n知识库上下文:\n{self.knowledge_context}")

        result = "\n\n".join(parts)

        current_hash = hashlib.sha256(result.encode("utf-8")).hexdigest()
        if self._last_prompt_hash is not None and self._last_prompt_hash != current_hash:
            logger.debug(
                f"System prompt changed (hash: {self._last_prompt_hash[:8]}... -> {current_hash[:8]}...), "
                f"likely cache miss"
            )
        self._last_prompt_hash = current_hash

        return result