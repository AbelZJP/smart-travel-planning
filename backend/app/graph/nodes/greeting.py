"""问候节点 (greeting)

当用户打招呼时，回复欢迎语并引导输入旅行需求。
"""
from langchain_core.messages import AIMessage
from app.graph.state import GraphState


WELCOME_MESSAGE = """你好呀！我是你的 🌍 **智能旅行规划助手**。

我可以帮你：
- 🗺️ **规划完整行程** — 告诉我目的地、天数、预算，我帮你安排
- 🎯 **动态调整** — 出行前随时修改行程，说一句就行
- 💰 **三档方案** — 经济/舒适/豪华，按预算灵活选择

**试试这样说：**
> "我想去杭州玩 3 天，预算 3000"
> "从北京出发去成都，帮我规划一下"
> "我喜欢自然风光和美食"

有什么旅行想法吗？😊"""


async def greeting_node(state: GraphState) -> dict:
    """返回欢迎语"""
    return {
        "messages": [AIMessage(content=WELCOME_MESSAGE)],
    }
