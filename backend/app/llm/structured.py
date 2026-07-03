"""LLM 结构化输出工具

某些 LLM（如 DeepSeek）不支持 OpenAI 的 response_format / function_calling 模式，
此模块提供回退方案：通过文本 prompt 要求 LLM 输出 JSON，再用 json.loads 解析。

用法：
    result = await invoke_structured(llm, SystemMessage(...), HumanMessage(...), pydantic_model)
"""
import json
import re
from typing import Type, TypeVar, Any
from langchain_core.messages import BaseMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def _extract_json(text: str) -> dict:
    """从 LLM 文本回复中提取 JSON 对象"""
    # 先尝试 ```json ... ``` 块
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if match:
        content = match.group(1).strip()
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

    # 尝试找第一对 { }
    brace_match = re.search(r"\{.*\}", text, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except json.JSONDecodeError:
            pass

    # 最后直接尝试整个文本
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        raise ValueError(f"无法从 LLM 回复中提取 JSON:\n{text[:500]}")


async def invoke_structured(
    llm: ChatOpenAI,
    messages: list[BaseMessage],
    schema: Type[T],
    fallback: dict | None = None,
) -> T:
    """调用 LLM 并解析为 Pydantic 模型

    先尝试 with_structured_output（兼容 OpenAI），
    失败后回退到文本 prompt + JSON 解析。

    Args:
        llm: ChatOpenAI 实例
        messages: 给 LLM 的消息列表
        schema: 目标 Pydantic 模型类
        fallback: 解析失败时的默认值

    Returns:
        解析后的 Pydantic 模型实例
    """
    # 方案一：尝试 with_structured_output（OpenAI 兼容）
    try:
        structured = llm.with_structured_output(schema)
        result = await structured.ainvoke(messages)
        return result
    except Exception as e:
        error_str = str(e).lower()
        # 只在不支持 response_format 时回退
        if "response_format" not in error_str and "json" not in error_str:
            raise  # 其他错误继续抛出

    # 方案二：文本 prompt + JSON 解析
    system_prompt = (
        "你是一个结构化数据输出器。请严格按照要求的 JSON 格式输出，"
        "不要包含任何 markdown 包裹、解释、或额外文字。\n\n"
        f"输出 JSON Schema:\n{json.dumps(schema.model_json_schema(), indent=2, ensure_ascii=False)}"
    )

    all_messages = [SystemMessage(content=system_prompt)] + list(messages)
    response = await llm.ainvoke(all_messages)
    content = response.content if hasattr(response, "content") else str(response)

    try:
        data = _extract_json(content)
        return schema(**data)
    except Exception as parse_err:
        if fallback is not None:
            return schema(**fallback)
        raise ValueError(
            f"解析结构化输出失败: {parse_err}\n"
            f"原始回复: {content[:300]}"
        )
