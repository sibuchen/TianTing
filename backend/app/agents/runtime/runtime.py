import asyncio
import hashlib
import logging
import os
import tempfile
import time
from typing import Any, AsyncGenerator

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.models.agent import Agent, AgentSubAgent, AgentSkill, AgentMCPServer, AgentTool
from app.models.skill import Skill
from app.models.model_config import ModelConfig
from app.core.security import decrypt_api_key
from app.services.agent_log_service import agent_log_service
from app.agents.runtime.reasoning_patch import apply_reasoning_content_patch
from app.agents.runtime.context import AgentContext, ToolDefinition

apply_reasoning_content_patch()

logger = logging.getLogger(__name__)

MAX_ORCHESTRATOR_LOOPS = 8


class AgentRuntime:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def process_message(
        self,
        conversation_id: str,
        user_content: str,
        channel: str = "web",
    ) -> str:
        orchestrator = await self._find_orchestrator(channel)
        if not orchestrator:
            return "系统尚未配置智能体，请联系管理员。"

        dispatch_start = time.time()
        await agent_log_service.write_log(
            conversation_id=conversation_id,
            agent_id=orchestrator.id,
            agent_name=orchestrator.name,
            operation_type="orchestrator_dispatch",
            operation_detail={"user_content": user_content, "channel": channel},
        )

        should_transfer, reason, detail = self._should_transfer_to_human(orchestrator, user_content)
        if should_transfer:
            await agent_log_service.write_log(
                conversation_id=conversation_id,
                agent_id=orchestrator.id,
                agent_name=orchestrator.name,
                operation_type="human_transfer",
                operation_detail={"reason": reason, "detail": detail, "source": "transfer_keywords"},
            )
            return "__TRANSFER_TO_HUMAN__"

        llm = await self._build_llm_instance(orchestrator)
        if not llm:
            return "系统智能体模型配置异常，请联系管理员。"

        tools = await self._build_orchestrator_tools(orchestrator)

        context = AgentContext(
            base_prompt=orchestrator.system_prompt or "你是一个专业的智能客服编排器。你的职责是理解用户的问题，调用合适的子智能体来处理，或直接回复用户。",
            channel=channel,
        )
        for agent_skill in orchestrator.skills:
            skill = agent_skill.skill
            if skill and skill.is_active():
                desc = skill.description or skill.display_name or skill.name
                context.skill_metadata.append(f"- {skill.name}: {desc}")

        for tool_def in tools:
            func_info = tool_def.get("function", {})
            tool_name = func_info.get("name", "")
            tool_desc = func_info.get("description", "")
            if tool_name:
                readonly_mark = " [只读]" if tool_def.get("is_readonly") else ""
                destructive_mark = " [需谨慎]" if tool_def.get("is_destructive") else ""
                context.tool_descriptions.append(f"- {tool_name}: {tool_desc}{readonly_mark}{destructive_mark}")

        system_prompt = context.build_system_prompt()

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_content),
        ]

        final_response = ""
        for loop_count in range(MAX_ORCHESTRATOR_LOOPS):
            if loop_count >= MAX_ORCHESTRATOR_LOOPS - 2:
                messages.append(SystemMessage(content="上下文轮次即将达到上限，请尽快给出最终回复，避免再次调用工具。"))
            try:
                llm_start = time.time()
                if tools:
                    llm_with_tools = llm.bind_tools(tools)
                    response = await llm_with_tools.ainvoke(messages)
                else:
                    response = await llm.ainvoke(messages)
                llm_duration_ms = int((time.time() - llm_start) * 1000)

                await agent_log_service.write_log(
                    conversation_id=conversation_id,
                    agent_id=orchestrator.id,
                    agent_name=orchestrator.name,
                    operation_type="llm_call",
                    operation_detail={"loop_count": loop_count + 1, "has_tool_calls": bool(response.tool_calls), "model": orchestrator.model_config.model_id if orchestrator.model_config else None},
                    duration_ms=llm_duration_ms,
                )
            except Exception as e:
                logger.error(f"LLM invocation error: {e}")
                return "抱歉，系统暂时无法处理您的消息，请稍后再试。"

            if response.tool_calls:
                reasoning_content = response.additional_kwargs.get("reasoning_content", None)

                parallel_results = await self._execute_tool_calls_parallel(
                    orchestrator, response.tool_calls, tools, conversation_id
                )

                if parallel_results is not None:
                    for tc, tool_result in parallel_results:
                        tool_name = tc["name"]

                        ai_msg = AIMessage(content="", tool_calls=[tc])
                        if reasoning_content:
                            ai_msg.additional_kwargs["reasoning_content"] = reasoning_content
                            ai_msg.content = [{"type": "reasoning", "reasoning_content": reasoning_content}]

                        if tool_name.startswith("call_subagent_"):
                            messages.append(ai_msg)
                            messages.append(HumanMessage(content=f"子智能体返回结果：{tool_result}"))
                        else:
                            messages.append(ai_msg)
                            messages.append(HumanMessage(content=f"工具返回结果：{tool_result}"))
                else:
                    for tool_call in response.tool_calls:
                        tool_name = tool_call["name"]
                        tool_args = tool_call.get("args", {})
                        tool_start = time.time()
                        tool_result = await self._execute_tool(orchestrator, tool_name, tool_args, conversation_id, tools=tools)
                        tool_duration_ms = int((time.time() - tool_start) * 1000)

                        if tool_name == "transfer_to_human":
                            await agent_log_service.write_log(
                                conversation_id=conversation_id,
                                agent_id=orchestrator.id,
                                agent_name=orchestrator.name,
                                operation_type="human_transfer",
                                operation_detail={"reason": tool_args.get("reason", ""), "source": "llm_judgment"},
                                duration_ms=tool_duration_ms,
                            )
                            return "__TRANSFER_TO_HUMAN__"

                        await agent_log_service.write_log(
                            conversation_id=conversation_id,
                            agent_id=orchestrator.id,
                            agent_name=orchestrator.name,
                            operation_type="tool_call",
                            operation_detail={"tool_name": tool_name, "tool_args": tool_args, "result_preview": str(tool_result)[:200]},
                            duration_ms=tool_duration_ms,
                        )

                        ai_msg = AIMessage(content="", tool_calls=[tool_call])
                        if reasoning_content:
                            ai_msg.additional_kwargs["reasoning_content"] = reasoning_content
                            ai_msg.content = [{"type": "reasoning", "reasoning_content": reasoning_content}]

                        if tool_name.startswith("call_subagent_"):
                            subagent_response = tool_result
                            messages.append(ai_msg)
                            messages.append(HumanMessage(content=f"子智能体返回结果：{subagent_response}"))
                        else:
                            messages.append(ai_msg)
                            messages.append(HumanMessage(content=f"工具返回结果：{tool_result}"))
            else:
                final_response = response.content or ""
                break
        else:
            if not final_response and messages:
                last_ai = None
                for msg in reversed(messages):
                    if isinstance(msg, AIMessage) and msg.content:
                        last_ai = msg.content
                        break
                final_response = last_ai or "抱歉，我暂时无法给出明确的答复，请稍后再试。"

            await agent_log_service.write_log(
                conversation_id=conversation_id,
                agent_id=orchestrator.id,
                agent_name=orchestrator.name,
                operation_type="max_loops_warning",
                operation_detail={"max_loops": MAX_ORCHESTRATOR_LOOPS, "final_response_preview": final_response[:200]},
            )
            logger.warning(f"Orchestrator reached max loops ({MAX_ORCHESTRATOR_LOOPS}) for conversation {conversation_id}")

        return final_response

    async def process_message_stream(
        self,
        conversation_id: str,
        user_content: str,
        channel: str = "web",
    ) -> AsyncGenerator[str, None]:
        orchestrator = await self._find_orchestrator(channel)
        if not orchestrator:
            yield "系统尚未配置智能体，请联系管理员。"
            return

        dispatch_start = time.time()
        await agent_log_service.write_log(
            conversation_id=conversation_id,
            agent_id=orchestrator.id,
            agent_name=orchestrator.name,
            operation_type="streaming_dispatch",
            operation_detail={"user_content": user_content, "channel": channel},
        )

        should_transfer, reason, detail = self._should_transfer_to_human(orchestrator, user_content)
        if should_transfer:
            await agent_log_service.write_log(
                conversation_id=conversation_id,
                agent_id=orchestrator.id,
                agent_name=orchestrator.name,
                operation_type="human_transfer",
                operation_detail={"reason": reason, "detail": detail, "source": "transfer_keywords"},
            )
            yield "__TRANSFER_TO_HUMAN__"
            return

        llm = await self._build_llm_instance(orchestrator)
        if not llm:
            yield "系统智能体模型配置异常，请联系管理员。"
            return

        tools = await self._build_orchestrator_tools(orchestrator)

        context = AgentContext(
            base_prompt=orchestrator.system_prompt or "你是一个专业的智能客服编排器。你的职责是理解用户的问题，调用合适的子智能体来处理，或直接回复用户。",
            channel=channel,
        )
        for agent_skill in orchestrator.skills:
            skill = agent_skill.skill
            if skill and skill.is_active():
                desc = skill.description or skill.display_name or skill.name
                context.skill_metadata.append(f"- {skill.name}: {desc}")

        for tool_def in tools:
            func_info = tool_def.get("function", {})
            tool_name = func_info.get("name", "")
            tool_desc = func_info.get("description", "")
            if tool_name:
                readonly_mark = " [只读]" if tool_def.get("is_readonly") else ""
                destructive_mark = " [需谨慎]" if tool_def.get("is_destructive") else ""
                context.tool_descriptions.append(f"- {tool_name}: {tool_desc}{readonly_mark}{destructive_mark}")

        system_prompt = context.build_system_prompt()

        messages: list = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_content),
        ]

        for loop_count in range(MAX_ORCHESTRATOR_LOOPS):
            if loop_count >= MAX_ORCHESTRATOR_LOOPS - 2:
                messages.append(SystemMessage(content="上下文轮次即将达到上限，请尽快给出最终回复，避免再次调用工具。"))

            try:
                llm_start = time.time()
                if tools:
                    llm_with_tools = llm.bind_tools(tools)
                    response = await llm_with_tools.ainvoke(messages)
                else:
                    response = await llm.ainvoke(messages)
                llm_duration_ms = int((time.time() - llm_start) * 1000)

                await agent_log_service.write_log(
                    conversation_id=conversation_id,
                    agent_id=orchestrator.id,
                    agent_name=orchestrator.name,
                    operation_type="llm_call",
                    operation_detail={"loop_count": loop_count + 1, "has_tool_calls": bool(response.tool_calls), "model": orchestrator.model_config.model_id if orchestrator.model_config else None},
                    duration_ms=llm_duration_ms,
                )
            except Exception as e:
                logger.error(f"LLM invocation error: {e}")
                yield "抱歉，系统暂时无法处理您的消息，请稍后再试。"
                return

            if response.tool_calls:
                reasoning_content = response.additional_kwargs.get("reasoning_content", None)

                parallel_results = await self._execute_tool_calls_parallel(
                    orchestrator, response.tool_calls, tools, conversation_id
                )

                if parallel_results is not None:
                    for tc, tool_result in parallel_results:
                        tool_name = tc["name"]

                        ai_msg = AIMessage(content="", tool_calls=[tc])
                        if reasoning_content:
                            ai_msg.additional_kwargs["reasoning_content"] = reasoning_content
                            ai_msg.content = [{"type": "reasoning", "reasoning_content": reasoning_content}]

                        if tool_name.startswith("call_subagent_"):
                            messages.append(ai_msg)
                            messages.append(HumanMessage(content=f"子智能体返回结果：{tool_result}"))
                        else:
                            messages.append(ai_msg)
                            messages.append(HumanMessage(content=f"工具返回结果：{tool_result}"))
                else:
                    for tool_call in response.tool_calls:
                        tool_name = tool_call["name"]
                        tool_args = tool_call.get("args", {})
                        tool_start = time.time()
                        tool_result = await self._execute_tool(orchestrator, tool_name, tool_args, conversation_id, tools=tools)
                        tool_duration_ms = int((time.time() - tool_start) * 1000)

                        if tool_name == "transfer_to_human":
                            await agent_log_service.write_log(
                                conversation_id=conversation_id,
                                agent_id=orchestrator.id,
                                agent_name=orchestrator.name,
                                operation_type="human_transfer",
                                operation_detail={"reason": tool_args.get("reason", ""), "source": "llm_judgment"},
                                duration_ms=tool_duration_ms,
                            )
                            yield "__TRANSFER_TO_HUMAN__"
                            return

                        await agent_log_service.write_log(
                            conversation_id=conversation_id,
                            agent_id=orchestrator.id,
                            agent_name=orchestrator.name,
                            operation_type="tool_call",
                            operation_detail={"tool_name": tool_name, "tool_args": tool_args, "result_preview": str(tool_result)[:200]},
                            duration_ms=tool_duration_ms,
                        )

                        ai_msg = AIMessage(content="", tool_calls=[tool_call])
                        if reasoning_content:
                            ai_msg.additional_kwargs["reasoning_content"] = reasoning_content
                            ai_msg.content = [{"type": "reasoning", "reasoning_content": reasoning_content}]

                        if tool_name.startswith("call_subagent_"):
                            subagent_response = tool_result
                            messages.append(ai_msg)
                            messages.append(HumanMessage(content=f"子智能体返回结果：{subagent_response}"))
                        else:
                            messages.append(ai_msg)
                            messages.append(HumanMessage(content=f"工具返回结果：{tool_result}"))
            else:
                final_content = response.content or ""
                messages.append(response)
                try:
                    stream_start = time.time()
                    if tools:
                        llm_with_tools = llm.bind_tools(tools)
                        stream = llm_with_tools.astream(messages)
                    else:
                        stream = llm.astream(messages)
                    async for chunk in stream:
                        if chunk.content:
                            yield chunk.content
                    stream_duration_ms = int((time.time() - stream_start) * 1000)
                    await agent_log_service.write_log(
                        conversation_id=conversation_id,
                        agent_id=orchestrator.id,
                        agent_name=orchestrator.name,
                        operation_type="stream_output",
                        operation_detail={"content_length": len(final_content)},
                        duration_ms=stream_duration_ms,
                    )
                except Exception as e:
                    logger.warning(f"Stream output error, falling back to chunked output: {e}")
                    for i in range(0, len(final_content), 2):
                        yield final_content[i:i + 2]
                return

        await agent_log_service.write_log(
            conversation_id=conversation_id,
            agent_id=orchestrator.id,
            agent_name=orchestrator.name,
            operation_type="max_loops_warning",
            operation_detail={"max_loops": MAX_ORCHESTRATOR_LOOPS},
        )
        logger.warning(f"Orchestrator stream reached max loops ({MAX_ORCHESTRATOR_LOOPS}) for conversation {conversation_id}")
        yield "抱歉，我暂时无法给出明确的答复，请稍后再试。"

    async def _execute_tool_calls_parallel(
        self,
        orchestrator: Agent,
        tool_calls: list,
        tools: list[ToolDefinition],
        conversation_id: str,
    ) -> list[tuple[dict, str]] | None:
        tool_def_map: dict[str, ToolDefinition] = {}
        for td in tools:
            name = td.get("function", {}).get("name", "")
            if name:
                tool_def_map[name] = td

        all_readonly = all(
            tool_def_map.get(tc["name"], {}).get("is_readonly", False)
            for tc in tool_calls
        )

        if not all_readonly or len(tool_calls) <= 1:
            return None

        async def execute_one(tc):
            tool_name = tc["name"]
            tool_args = tc.get("args", {})
            result = await self._execute_tool(orchestrator, tool_name, tool_args, conversation_id)
            return (tc, result)

        results = await asyncio.gather(*[execute_one(tc) for tc in tool_calls])
        return results

    @staticmethod
    def _should_transfer_to_human(orchestrator: Agent, user_content: str) -> tuple[bool, str | None, str | None]:
        """统一转人工决策：先检查关键词匹配"""
        transfer_keywords = orchestrator.transfer_keywords or []
        if isinstance(transfer_keywords, list):
            for keyword in transfer_keywords:
                if keyword in user_content:
                    return True, "keyword_match", keyword
        return False, None, None

    async def _find_orchestrator(self, channel: str) -> Agent | None:
        logger.debug(f"[_find_orchestrator] Starting query for channel={channel}")
        try:
            logger.debug("[_find_orchestrator] Building query with joinedload...")
            stmt = (
                select(Agent)
                .options(
                    joinedload(Agent.model_config),
                    joinedload(Agent.sub_agents).joinedload(AgentSubAgent.sub_agent),
                    joinedload(Agent.skills)
                    .joinedload(AgentSkill.skill)
                    .selectinload(Skill.resources),
                    joinedload(Agent.mcp_servers).joinedload(AgentMCPServer.mcp_server),
                    joinedload(Agent.tools).joinedload(AgentTool.tool_config),
                )
                .where(
                    Agent.type == "orchestrator",
                    Agent.is_enabled == True,
                )
            )
            logger.debug("[_find_orchestrator] Executing query...")
            result = await self.db.execute(stmt)
            logger.debug("[_find_orchestrator] Query executed, calling unique().scalars().all()...")
            agents = result.unique().scalars().all()
            logger.debug(f"[_find_orchestrator] Got {len(agents)} agents")
        except Exception as e:
            logger.error(f"[_find_orchestrator] Query failed: {type(e).__name__}: {e}", exc_info=True)
            raise
  
        for agent in agents:
            channels = agent.supported_channels
            if channels is None or not isinstance(channels, list) or len(channels) == 0:
                return agent
            if channel in channels:
                return agent

        if agents:
            return agents[0]
        return None

    @staticmethod
    def _normalize_base_url(base_url: str) -> str:
        url = base_url.rstrip("/")
        if url.endswith("/chat/completions"):
            url = url[:-len("/chat/completions")]
        return url

    @staticmethod
    def _maybe_truncate_tool_result(result: str) -> str:
        max_chars = int(os.environ.get("TOOL_RESULT_MAX_CHARS", "8000"))
        if len(result) <= max_chars:
            return result
        timestamp = int(time.time())
        hash_str = hashlib.sha256(result.encode()).hexdigest()
        filename = f"tool_result_{timestamp}_{hash_str[:8]}.txt"
        file_path = os.path.join(tempfile.gettempdir(), filename)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(result)
        return f"[工具结果过大({len(result)}字符)，完整内容已保存至: {file_path}]\n\n{result[:200]}..."

    async def _build_llm_instance(self, agent: Agent) -> ChatOpenAI | None:
        if not agent.model_config:
            return None

        model_config = agent.model_config
        try:
            api_key = decrypt_api_key(model_config.api_key_enc, model_config.api_key_iv)
        except Exception as e:
            logger.error(f"Failed to decrypt API key: {e}")
            return None

        return ChatOpenAI(
            model=model_config.model_id,
            base_url=self._normalize_base_url(model_config.base_url),
            api_key=api_key,
            temperature=0.7,
        )

    async def _build_orchestrator_tools(self, orchestrator: Agent) -> list[ToolDefinition]:
        tools = []

        for agent_sub in orchestrator.sub_agents:
            sub_agent = agent_sub.sub_agent
            if sub_agent.is_enabled:
                tool_def: ToolDefinition = {
                    "type": "function",
                    "function": {
                        "name": f"call_subagent_{sub_agent.id.replace('-', '_')}",
                        "description": sub_agent.description or f"调用子智能体：{sub_agent.name}",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": f"传递给{sub_agent.name}的问题或任务描述",
                                }
                            },
                            "required": ["query"],
                        },
                    },
                    "is_readonly": True,
                    "is_destructive": False,
                }
                tools.append(tool_def)

        for agent_skill in orchestrator.skills:
            skill = agent_skill.skill
            if skill and skill.is_active():
                tool_name = f"use_skill_{skill.name.replace('-', '_')}"
                skill_desc = f"加载并使用技能: {skill.display_name or skill.name} - {skill.description or ''}"
                if skill.resources:
                    resource_names = ", ".join(r.file_name for r in skill.resources)
                    skill_desc += f" | 可用资源文件: {resource_names}"
                tool_def: ToolDefinition = {
                    "type": "function",
                    "function": {
                        "name": tool_name,
                        "description": skill_desc,
                        "parameters": {
                            "type": "object",
                            "properties": {},
                            "required": [],
                        },
                    },
                    "is_readonly": True,
                    "is_destructive": False,
                }
                tools.append(tool_def)

        transfer_tool: ToolDefinition = {
            "type": "function",
            "function": {
                "name": "transfer_to_human",
                "description": "将对话转接给人工客服。当用户明确要求转人工、问题超出智能体能力范围、或用户情绪激动时使用。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reason": {
                            "type": "string",
                            "description": "转人工的原因",
                        }
                    },
                    "required": ["reason"],
                },
            },
            "is_readonly": False,
            "is_destructive": True,
        }
        tools.append(transfer_tool)

        return tools

    async def _execute_tool(
        self,
        orchestrator: Agent,
        tool_name: str,
        tool_args: dict[str, Any],
        conversation_id: str,
        tools: list[ToolDefinition] | None = None,
    ) -> str:
        if tools:
            for td in tools:
                if td.get("function", {}).get("name") == tool_name:
                    tool_def = td
                    break
            else:
                tool_def = None

            if tool_def and tool_def.get("permission_handler"):
                try:
                    allowed, reason = tool_def["permission_handler"](tool_args, conversation_id)
                    if not allowed:
                        return f"工具执行被拒绝：{reason or '权限不足'}"
                except Exception as e:
                    logger.error(f"permission_handler error for {tool_name}: {e}")
                    return f"工具权限校验异常：{str(e)}"

        if tool_name == "transfer_to_human":
            return "__TRANSFER_TO_HUMAN__"

        if tool_name.startswith("call_subagent_"):
            sub_agent_id_raw = tool_name.replace("call_subagent_", "").replace("_", "-")
            from app.agents.runtime.subagent import SubagentRuntime
            subagent_runtime = SubagentRuntime(self.db)
            result = await subagent_runtime.execute(
                sub_agent_id=sub_agent_id_raw,
                query=tool_args.get("query", ""),
                conversation_id=conversation_id,
                parent_agent_id=orchestrator.id,
            )
            return self._maybe_truncate_tool_result(result)

        if tool_name.startswith("use_skill_"):
            skill_name = tool_name.replace("use_skill_", "").replace("_", "-")
            skill_body = None
            matched_skill = None
            for agent_skill in orchestrator.skills:
                s = agent_skill.skill
                if s and s.name == skill_name and s.is_active():
                    skill_body = s.skill_body or s.prompts
                    matched_skill = s
                    break
            if not skill_body:
                return f"技能 {skill_name} 未找到或未激活"
            
            resources = matched_skill.resources if matched_skill else []
            if not resources:
                return self._maybe_truncate_tool_result(f"[技能已加载] {skill_name}:\n{skill_body}")
            
            first_resource = resources[0]
            skill_dir = os.path.dirname(first_resource.file_path)
            
            processed_body = skill_body.replace("${SKILL_DIR}", skill_dir)
            
            resource_list = "\n".join(f"- {r.file_name}" for r in resources)
            return self._maybe_truncate_tool_result(
                f"Base directory for this skill: {skill_dir}\n\n"
                f"[技能已加载] {skill_name}:\n{processed_body}\n\n"
                f"Available resource files:\n{resource_list}"
            )

        if tool_name.startswith("read_skill_resource_"):
            parts = tool_name.replace("read_skill_resource_", "", 1).rsplit("_", 1)
            if len(parts) == 2:
                skill_name = parts[0].replace("_", "-")
                resource_name = parts[1]
                for agent_skill in orchestrator.skills:
                    s = agent_skill.skill
                    if s and s.name == skill_name and s.is_active():
                        for resource in s.resources:
                            if resource.file_name == resource_name:
                                if resource.file_content:
                                    return self._maybe_truncate_tool_result(
                                        f"[资源文件: {resource_name}]\n{resource.file_content}"
                                    )
                                try:
                                    full_path = resource.file_path
                                    if not full_path or not os.path.exists(full_path):
                                        return f"[资源文件: {resource_name}]\n错误: 文件内容不可用（不在数据库中，也不在磁盘上）"
                                    file_size = os.path.getsize(full_path)
                                    if file_size > 1048576:
                                        with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                                            content = f.read(2000)
                                        return f"[资源文件: {resource_name}]\n文件大小: {file_size} bytes (超过1MB，仅显示前2000字符)\n\n{content}..."
                                    mime = resource.mime_type or ""
                                    if mime.startswith("text/") or mime in ("application/json", "application/javascript", "application/xml"):
                                        with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                                            content = f.read()
                                        return self._maybe_truncate_tool_result(f"[资源文件: {resource_name}]\n{content}")
                                    else:
                                        return f"[资源文件: {resource_name}]\n文件类型: {mime or '未知'}\n文件大小: {file_size} bytes"
                                except Exception as e:
                                    return f"[资源文件: {resource_name}]\n读取错误: {str(e)}"
                return f"资源文件 {resource_name} 未找到"
            return f"资源文件读取参数错误"

        return f"未知工具：{tool_name}"
