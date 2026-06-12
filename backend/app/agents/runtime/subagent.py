import hashlib
import json
import logging
import os
import tempfile
import time
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.models.agent import Agent, AgentSkill, AgentMCPServer, AgentTool, AgentKnowledgeDocument, AgentKnowledgeQA
from app.models.skill import Skill
from app.core.security import decrypt_api_key
from app.services.agent_log_service import agent_log_service
from app.agents.runtime.reasoning_patch import apply_reasoning_content_patch
from app.agents.runtime.context import AgentContext, ToolDefinition

apply_reasoning_content_patch()

logger = logging.getLogger(__name__)


class SubagentRuntime:
    def __init__(self, db: AsyncSession):
        self.db = db
        self._mcp_tool_map: dict[str, tuple[str, str]] = {}

    async def execute(
        self,
        sub_agent_id: str,
        query: str,
        conversation_id: str,
        parent_agent_id: str,
    ) -> str:
        sub_agent = await self._load_subagent(sub_agent_id)
        if not sub_agent:
            return f"子智能体未找到或未启用。"

        execute_start = time.time()
        await agent_log_service.write_log(
            conversation_id=conversation_id,
            agent_id=sub_agent.id,
            agent_name=sub_agent.name,
            operation_type="subagent_execute",
            operation_detail={"query": query, "parent_agent_id": parent_agent_id},
        )

        llm = await self._build_llm_instance(sub_agent)
        if not llm:
            return "子智能体模型配置异常。"

        tools = await self._build_subagent_tools(sub_agent)

        context = AgentContext(
            base_prompt=sub_agent.system_prompt or f"你是{sub_agent.name}，一个专业的智能客服助手。请根据用户的问题提供帮助。",
            channel="subagent",
        )
        for agent_skill in sub_agent.skills:
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
            HumanMessage(content=query),
        ]

        max_loops = 8
        for loop_count in range(max_loops):
            if loop_count >= max_loops - 2:
                messages.append(SystemMessage(content="上下文轮次即将达到上限，请尽快给出最终回复，避免再次调用工具。"))
            try:
                if tools:
                    llm_with_tools = llm.bind_tools(tools)
                    response = await llm_with_tools.ainvoke(messages)
                else:
                    response = await llm.ainvoke(messages)
            except Exception as e:
                logger.error(f"Subagent LLM invocation error: {e}")
                return "抱歉，子智能体处理时出现错误。"

            if response.tool_calls:
                reasoning_content = response.additional_kwargs.get("reasoning_content", None)
                for tool_call in response.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call.get("args", {})
                    tool_start = time.time()
                    tool_result = await self._execute_subagent_tool(sub_agent, tool_name, tool_args, conversation_id, tools=tools)
                    tool_duration_ms = int((time.time() - tool_start) * 1000)

                    if tool_name == "search_knowledge_base":
                        await agent_log_service.write_log(
                            conversation_id=conversation_id,
                            agent_id=sub_agent.id,
                            agent_name=sub_agent.name,
                            operation_type="knowledge_search",
                            operation_detail={"query": tool_args.get("query", ""), "result_preview": str(tool_result)[:200]},
                            duration_ms=tool_duration_ms,
                        )
                    elif tool_name == "search_qa":
                        await agent_log_service.write_log(
                            conversation_id=conversation_id,
                            agent_id=sub_agent.id,
                            agent_name=sub_agent.name,
                            operation_type="qa_search",
                            operation_detail={"query": tool_args.get("query", ""), "result_preview": str(tool_result)[:200]},
                            duration_ms=tool_duration_ms,
                        )
                    else:
                        await agent_log_service.write_log(
                            conversation_id=conversation_id,
                            agent_id=sub_agent.id,
                            agent_name=sub_agent.name,
                            operation_type="tool_call",
                            operation_detail={"tool_name": tool_name, "tool_args": tool_args, "result_preview": str(tool_result)[:200]},
                            duration_ms=tool_duration_ms,
                        )

                    ai_msg = AIMessage(content="", tool_calls=[tool_call])
                    if reasoning_content:
                        ai_msg.additional_kwargs["reasoning_content"] = reasoning_content
                        ai_msg.content = [{"type": "reasoning", "reasoning_content": reasoning_content}]
                    messages.append(ai_msg)
                    messages.append(HumanMessage(content=f"工具返回结果：{tool_result}"))
            else:
                return response.content or ""

        return "子智能体处理超时，请稍后再试。"

    async def _load_subagent(self, sub_agent_id: str) -> Agent | None:
        logger.debug(f"[_load_subagent] Loading subagent: {sub_agent_id}")
        try:
            logger.debug("[_load_subagent] Building query with joinedload...")
            stmt = (
                select(Agent)
                .options(
                    joinedload(Agent.model_config),
                    joinedload(Agent.skills)
                    .joinedload(AgentSkill.skill)
                    .selectinload(Skill.resources),
                    joinedload(Agent.mcp_servers).joinedload(AgentMCPServer.mcp_server),
                    joinedload(Agent.tools).joinedload(AgentTool.tool_config),
                    joinedload(Agent.knowledge_documents).joinedload(AgentKnowledgeDocument.document),
                    joinedload(Agent.knowledge_qa_list).joinedload(AgentKnowledgeQA.qa),
                )
                .where(
                    Agent.id == sub_agent_id,
                    Agent.is_enabled == True,
                )
            )
            logger.debug("[_load_subagent] Executing query...")
            result = await self.db.execute(stmt)
            logger.debug("[_load_subagent] Query executed, calling unique().scalar_one_or_none()...")
            agent = result.unique().scalar_one_or_none()
            logger.debug(f"[_load_subagent] Result: {agent.name if agent else 'None'}")
            return agent
        except Exception as e:
            logger.error(f"[_load_subagent] Query failed: {type(e).__name__}: {e}", exc_info=True)
            raise

    async def _build_llm_instance(self, agent: Agent) -> ChatOpenAI | None:
        if not agent.model_config:
            return None
        model_config = agent.model_config
        try:
            api_key = decrypt_api_key(model_config.api_key_enc, model_config.api_key_iv)
        except Exception as e:
            logger.error(f"Failed to decrypt API key: {e}")
            return None
        url = model_config.base_url.rstrip("/")
        if url.endswith("/chat/completions"):
            url = url[:-len("/chat/completions")]
        return ChatOpenAI(
            model=model_config.model_id,
            base_url=url,
            api_key=api_key,
            temperature=0.7,
        )

    async def _build_subagent_tools(self, sub_agent: Agent) -> list[ToolDefinition]:
        tools = []
        self._mcp_tool_map = {}

        if sub_agent.knowledge_documents:
            tool_def: ToolDefinition = {
                "type": "function",
                "function": {
                    "name": "search_knowledge_base",
                    "description": "搜索知识库文档，查找与用户问题相关的信息。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "搜索关键词",
                            }
                        },
                        "required": ["query"],
                    },
                },
                "is_readonly": True,
                "is_destructive": False,
            }
            tools.append(tool_def)

        if sub_agent.knowledge_qa_list:
            tool_def: ToolDefinition = {
                "type": "function",
                "function": {
                    "name": "search_qa",
                    "description": "搜索问答集，查找与用户问题匹配的问答对。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "搜索关键词",
                            }
                        },
                        "required": ["query"],
                    },
                },
                "is_readonly": True,
                "is_destructive": False,
            }
            tools.append(tool_def)

        for agent_tool in sub_agent.tools:
            if agent_tool.is_enabled and agent_tool.tool_config:
                tc = agent_tool.tool_config
                tool_def: ToolDefinition = {
                    "type": "function",
                    "function": {
                        "name": f"builtin_{tc.name}",
                        "description": tc.description or tc.name,
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "input": {
                                    "type": "string",
                                    "description": f"调用{tc.name}的输入参数",
                                }
                            },
                            "required": ["input"],
                        },
                    },
                    "is_readonly": False,
                    "is_destructive": True,
                }
                tools.append(tool_def)

        for agent_mcp in sub_agent.mcp_servers:
            if not agent_mcp.is_linked:
                continue
            mcp_server = agent_mcp.mcp_server
            if not mcp_server:
                continue
            is_stdio = mcp_server.transport_type == "stdio" or (
                not mcp_server.url and mcp_server.command
            )
            if not is_stdio and not mcp_server.url:
                continue
            try:
                from app.agents.mcp_client import get_mcp_client
                api_key = None
                if mcp_server.env and isinstance(mcp_server.env, dict):
                    api_key = mcp_server.env.get("api_key")
                if is_stdio:
                    client = await get_mcp_client(
                        mcp_server.id,
                        transport_type="stdio",
                        command=mcp_server.command,
                        args=mcp_server.args or [],
                        env=mcp_server.env or {},
                    )
                else:
                    client = await get_mcp_client(mcp_server.id, mcp_server.url, api_key)
                discovered = await client.discover_tools()
                for mcp_tool in discovered:
                    tool_name = mcp_tool.get("name", "")
                    if not tool_name:
                        continue
                    generated_name = f"mcp_{mcp_server.id.replace('-', '_')}_{tool_name}"
                    self._mcp_tool_map[generated_name] = (mcp_server.id, tool_name)
                    input_schema = mcp_tool.get("inputSchema", mcp_tool.get("parameters", {}))
                    if not input_schema:
                        input_schema = {"type": "object", "properties": {}}
                    mcp_tool_def: ToolDefinition = {
                        "type": "function",
                        "function": {
                            "name": generated_name,
                            "description": mcp_tool.get("description", f"MCP工具: {tool_name}"),
                            "parameters": input_schema,
                        },
                        "is_readonly": False,
                        "is_destructive": False,
                    }
                    tools.append(mcp_tool_def)
            except Exception as e:
                logger.error(f"Failed to discover MCP tools for server {mcp_server.id}: {e}")

        for agent_skill in sub_agent.skills:
            skill = agent_skill.skill
            if skill and skill.is_active():
                tool_name = f"use_skill_{skill.name.replace('-', '_')}"
                desc = f"加载并使用技能: {skill.display_name or skill.name} - {skill.description or ''}"
                if skill.resources:
                    resource_names = ", ".join(r.file_name for r in skill.resources)
                    desc += f" | 可用资源文件: {resource_names}"
                skill_tool_def: ToolDefinition = {
                    "type": "function",
                    "function": {
                        "name": tool_name,
                        "description": desc,
                        "parameters": {
                            "type": "object",
                            "properties": {},
                            "required": [],
                        },
                    },
                    "is_readonly": True,
                    "is_destructive": False,
                }
                tools.append(skill_tool_def)

        return tools

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

    async def _execute_subagent_tool(
        self,
        sub_agent: Agent,
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

        if tool_name == "search_knowledge_base":
            result = await self._search_knowledge(sub_agent, tool_args.get("query", ""))
            return self._maybe_truncate_tool_result(result)

        if tool_name == "search_qa":
            result = await self._search_qa(sub_agent, tool_args.get("query", ""))
            return self._maybe_truncate_tool_result(result)

        if tool_name.startswith("builtin_"):
            result = await self._execute_builtin_tool(tool_name, tool_args)
            return self._maybe_truncate_tool_result(result)

        if tool_name.startswith("mcp_"):
            result = await self._execute_mcp_tool(tool_name, tool_args)
            return self._maybe_truncate_tool_result(result)

        if tool_name.startswith("use_skill_"):
            skill_name = tool_name.replace("use_skill_", "").replace("_", "-")
            skill_body = None
            matched_skill = None
            for agent_skill in sub_agent.skills:
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
                for agent_skill in sub_agent.skills:
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

    async def _search_knowledge(self, sub_agent: Agent, query: str) -> str:
        try:
            from app.rag.embedder import embedder
            from app.rag.retriever import retriever

            doc_ids = [ad.document_id for ad in sub_agent.knowledge_documents]
            embeddings = await embedder.embed_text(query)
            if not embeddings:
                return "未找到相关知识库内容。"
            results = await retriever.similarity_search(self.db, embeddings[0], doc_ids=doc_ids)
            if not results:
                return "未找到相关知识库内容。"
            context_parts = [r["content"] for r in results[:3]]
            return "\n\n".join(context_parts)
        except Exception as e:
            logger.error(f"Knowledge search error: {e}")
            return "知识库查询失败。"

    async def _search_qa(self, sub_agent: Agent, query: str) -> str:
        try:
            from app.rag.qa_search import QASearch
            qa_search = QASearch(self.db)
            results = await qa_search.search(query)
            if not results:
                return "未找到相关问答。"
            qa_parts = [f"问：{r['question']}\n答：{r['answer']}" for r in results[:3]]
            return "\n\n".join(qa_parts)
        except Exception as e:
            logger.error(f"QA search error: {e}")
            return "问答查询失败。"

    async def _execute_builtin_tool(self, tool_name: str, tool_args: dict[str, Any]) -> str:
        from app.agents.runtime.tool_registry import execute_builtin_tool
        actual_tool_name = tool_name.replace("builtin_", "")
        try:
            input_str = tool_args.get("input", "{}")
            if isinstance(input_str, str):
                parsed_args = json.loads(input_str)
            else:
                parsed_args = input_str
        except json.JSONDecodeError:
            parsed_args = {}
        return await execute_builtin_tool("", actual_tool_name, parsed_args)

    async def _execute_mcp_tool(self, tool_name: str, tool_args: dict[str, Any]) -> str:
        mapping = self._mcp_tool_map.get(tool_name)
        if not mapping:
            return f"未知的MCP工具：{tool_name}"
        server_id, original_tool_name = mapping
        try:
            from app.agents.mcp_client import get_mcp_client
            from app.models.mcp_server import MCPServer
            result = await self.db.execute(
                select(MCPServer).where(MCPServer.id == server_id)
            )
            mcp_server = result.scalar_one_or_none()
            if not mcp_server:
                return f"MCP服务器未找到：{server_id}"

            is_stdio = mcp_server.transport_type == "stdio" or (
                not mcp_server.url and mcp_server.command
            )

            if is_stdio:
                client = await get_mcp_client(
                    server_id,
                    transport_type="stdio",
                    command=mcp_server.command,
                    args=mcp_server.args or [],
                    env=mcp_server.env or {},
                )
            else:
                if not mcp_server.url:
                    return f"MCP服务器未配置URL：{server_id}"
                api_key = None
                if mcp_server.env and isinstance(mcp_server.env, dict):
                    api_key = mcp_server.env.get("api_key")
                client = await get_mcp_client(server_id, mcp_server.url, api_key)

            call_result = await client.call_tool(original_tool_name, tool_args)
            if call_result.get("success"):
                import json as _json
                result_data = call_result.get("result")
                if isinstance(result_data, str):
                    return result_data
                return _json.dumps(result_data, ensure_ascii=False)
            else:
                return f"MCP工具调用失败：{call_result.get('error', '未知错误')}"
        except Exception as e:
            logger.error(f"MCP tool execution error: {e}")
            return f"MCP工具执行异常：{str(e)}"
