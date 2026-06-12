"""
DEPRECATED: 此模块已废弃，由 app.agents.runtime 替代。
不再被任何活跃代码引用，保留仅供参考。
"""

"""
FAQ Node
FAQ节点：RAG检索 + 问答
"""

from app.agents.state import AgentState


async def faq_node(state: AgentState) -> AgentState:
    """
    FAQ节点
    基于RAG检索回答问题
    """
    messages = state.get("messages", [])
    last_message = messages[-1] if messages else {}
    user_content = last_message.get("content", "")

    rag_results = [
        {
            "content": "根据我们的退换货政策，商品在收到后7天内可以申请退换货。",
            "source": "退货政策文档",
        },
        {
            "content": "申请退换货的步骤：1. 登录账户；2. 进入订单详情；3. 点击退换货申请。",
            "source": "退货流程文档",
        },
    ]

    response = _generate_faq_response(user_content, rag_results)

    return {
        "current_node": "faq",
        "agent_response": response,
        "rag_results": rag_results,
        "tool_calls": None,
    }


def _generate_faq_response(query: str, rag_results: list[dict]) -> str:
    """基于检索结果生成回答"""
    if not rag_results:
        return "抱歉，我没有找到相关的答案。请您换个方式描述您的问题，或者转接人工客服获取帮助。"

    context = "\n\n".join([r["content"] for r in rag_results])

    response = f"根据我的知识库，我找到了以下相关信息：\n\n{context}\n\n希望这些信息对您有帮助！如果还有其他问题，请随时提问。"

    return response
