"""统一 LLM 实例化工厂

提供 get_smart_llm() / get_fast_llm() 两个工厂函数，
收敛所有 ChatOpenAI 创建逻辑，避免各处重复写 model/api_key/base_url。
"""
from langchain_openai import ChatOpenAI
from app.config import settings


def get_smart_llm(**kwargs) -> ChatOpenAI:
    """返回"智能" LLM 实例（用于生成计划、重规划等复杂推理）

    Args:
        **kwargs: 覆盖 ChatOpenAI 默认参数的键值对
    """
    merged = {
        "model": settings.llm_model,
        "api_key": settings.llm_api_key,
        "base_url": settings.llm_base_url,
        "temperature": 0.7,
    }
    merged.update(kwargs)
    return ChatOpenAI(**merged)


def get_fast_llm(**kwargs) -> ChatOpenAI:
    """返回"快速" LLM 实例（用于意图分类、槽位提取等简单推理）

    Args:
        **kwargs: 覆盖 ChatOpenAI 默认参数的键值对
    """
    model = settings.llm_fast_model or settings.llm_model
    merged = {
        "model": model,
        "api_key": settings.llm_api_key,
        "base_url": settings.llm_base_url,
        "temperature": 0.3,
    }
    merged.update(kwargs)
    return ChatOpenAI(**merged)
