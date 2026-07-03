"""需求提取节点 (extract_requirements)

多轮对话中增量提取/更新旅行需求。
每次只填充用户明确提到的字段，已有字段不覆盖。
当需求不完整时，自动生成追问消息。
"""
from datetime import date
from typing import Optional, List
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from app.graph.state import GraphState
from app.llm.factory import get_smart_llm
from app.llm.structured import invoke_structured


class TravelRequirementsExtraction(BaseModel):
    """从对话中提取的旅行需求"""
    origin: Optional[str] = Field(None, description="出发城市，如 '上海'。没提到则为 None")
    destination: Optional[str] = Field(None, description="目的地城市，如 '杭州'。没提到则为 None")
    budget: Optional[float] = Field(None, description="总预算（元），如 3000。没提到则为 None")
    days: Optional[int] = Field(None, description="出行天数，如 3。没提到则为 None")
    start_date: Optional[str] = Field(None, description="出发日期 YYYY-MM-DD 格式。没提到则为 None")
    preferences: List[str] = Field(default_factory=list, description="旅行偏好标签，如 ['nature', 'history', 'food', 'family']。只提取明确提到的")
    intercity_mode: Optional[str] = Field(None, description="城市间交通方式: high_speed_rail/flight/self_drive/bus/train。没提到则为 None")
    city_transit: Optional[str] = Field(None, description="城市内交通方式: public_transit/taxi/rental_car/mixed。没提到则为 None")


SYSTEM_PROMPT = """你是一个旅行需求提取器。从用户对话中提取结构化的旅行需求。

当前日期：{today_date}

规则：
1. **只提取用户明确提到的字段**，不要编造或猜测
2. 已经存在的字段（已有的需求）保留不变，只更新新提到的字段
3. 偏好过滤：只从 [nature(自然风光), history(历史文化), food(美食购物), family(亲子休闲)] 中选择
4. 如果用户说"随便""你定"之类，标记为已确认但保留 None
5. **日期处理**：start_date 必须输出 YYYY-MM-DD 格式。如果用户说相对日期（"明天"、"后天"、"下周一"等），根据当前日期({today_date})推算绝对日期。
6. 出发城市 origin 也有相对说法，如"我这里"可结合上下文推断；如果不确定则保留 None

已有需求：{existing_requirements}
用户消息：{user_message}"""


async def extract_requirements_node(state: GraphState) -> dict:
    """从用户消息中提取/更新旅行需求"""
    messages = state.get("messages", [])
    existing = state.get("requirements", {})

    # 找最后一条用户消息
    last_user_msg = ""
    for msg in reversed(messages):
        if hasattr(msg, "type") and msg.type == "human":
            last_user_msg = msg.content
            break

    if not last_user_msg:
        return {}

    today = date.today()
    today_str = today.isoformat()

    llm = get_smart_llm()
    result = await invoke_structured(
        llm,
        [
            SystemMessage(content=SYSTEM_PROMPT.format(
                today_date=today_str,
                existing_requirements=str(existing),
                user_message=last_user_msg,
            )),
            HumanMessage(content=f"已有需求: {existing}\n用户消息: {last_user_msg}"),
        ],
        TravelRequirementsExtraction,
    )

    # 增量合并：新值覆盖旧值，None 表示未提及则保留旧值
    merged = dict(existing)
    for field in ["origin", "destination", "budget", "days", "start_date", "intercity_mode", "city_transit"]:
        val = getattr(result, field, None)
        if val is not None:
            merged[field] = val

    # preferences 特殊处理：如果新提取的列表非空则覆盖
    if result.preferences:
        merged["preferences"] = result.preferences

    # 检查是否所有必填字段都填满了
    required = ["origin", "destination", "budget", "days", "start_date"]
    merged["completed"] = all(merged.get(f) is not None for f in required)

    # 如果需求不完整，生成追问消息引导用户补充
    if not merged["completed"]:
        missing = _get_missing_fields(merged)
        follow_up = _build_followup_question(missing, merged)
        return {
            "requirements": merged,
            "messages": [AIMessage(content=follow_up)],
        }

    return {"requirements": merged}


def _get_missing_fields(req: dict) -> list[str]:
    """检查哪些必填字段缺失，返回人类可读的字段名列表"""
    field_labels = {
        "origin": "出发城市",
        "destination": "目的地城市",
        "budget": "预算",
        "days": "出行天数",
        "start_date": "出发日期",
    }
    missing = []
    required = ["origin", "destination", "budget", "days", "start_date"]
    for f in required:
        if req.get(f) is None:
            missing.append(field_labels.get(f, f))
    return missing


def _build_followup_question(missing: list[str], existing: dict) -> str:
    """根据缺失字段生成追问消息"""
    # 已提取到的信息摘要
    known = []
    field_labels = {
        "origin": "出发城市", "destination": "目的地",
        "budget": "预算", "days": "天数",
        "start_date": "出发日期", "preferences": "偏好",
    }
    for f, label in field_labels.items():
        val = existing.get(f)
        if val is not None:
            if f == "budget":
                known.append(f"{label}: ¥{val}")
            elif f == "preferences":
                known.append(f"{label}: {val}")
            elif f == "days":
                known.append(f"{label}: {val}天")
            else:
                known.append(f"{label}: {val}")

    known_str = "、".join(known) if known else "暂无"

    # 构建追问
    if len(missing) == 1:
        question = f"还差一个信息：请问您的**{missing[0]}**是什么？"
    else:
        question = f"还需要您补充以下信息：**{'、'.join(missing)}**"

    return (
        f"好的，我已经记录了以下信息：\n\n"
        f"> {known_str}\n\n"
        f"{question}\n\n"
        f"请告诉我，我继续为您规划行程 😊"
    )
