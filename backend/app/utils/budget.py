"""预算分档计算"""

# 每档参数的每日人均预算（元）
TIER_CONFIG = {
    "economy": {
        "label": "经济",
        "hotel_per_night": 150,
        "meals_per_day": 65,
        "city_transit_per_day": 20,
        "free_attractions_first": True,
    },
    "comfort": {
        "label": "舒适",
        "hotel_per_night": 350,
        "meals_per_day": 150,
        "city_transit_per_day": 60,
        "free_attractions_first": False,
    },
    "luxury": {
        "label": "豪华",
        "hotel_per_night": 600,
        "meals_per_day": 300,
        "city_transit_per_day": 150,
        "free_attractions_first": False,
    },
}


def get_tier_config(tier: str) -> dict:
    """获取指定档位的预算配置"""
    return TIER_CONFIG.get(tier, TIER_CONFIG["comfort"])


# 每档的目标预算占比（相对总预算）
TIER_BUDGET_RATIO = {
    "economy": 0.50,   # 经济档花 50% 预算
    "comfort": 0.75,   # 舒适档花 75% 预算
    "luxury": 0.95,    # 豪华档花 95% 预算（接近预算上限）
}


def calculate_budget_allocation(
    total_budget: float, days: int, tier: str, intercity_mode: str
) -> dict:
    """根据档位分配预算到各分类。

    Returns dict with keys: hotel, meals, transit, tickets, intercity, target_total
    """
    config = get_tier_config(tier)
    ratio = TIER_BUDGET_RATIO.get(tier, 0.75)
    tier_budget = total_budget * ratio  # 该档位的目标总花费

    # 城市间交通预估（根据出行方式）
    intercity_estimates = {
        "high_speed_rail": 300,
        "flight": 800,
        "self_drive": 200,
        "bus": 100,
        "train": 150,
    }
    intercity_cost = intercity_estimates.get(intercity_mode, 300) * 2  # 往返

    remaining = tier_budget - intercity_cost

    hotel_budget = config["hotel_per_night"] * days
    meals_budget = config["meals_per_day"] * days
    transit_budget = config["city_transit_per_day"] * days
    tickets_budget = remaining - hotel_budget - meals_budget - transit_budget

    if tickets_budget < 0:
        scale = remaining / (hotel_budget + meals_budget + transit_budget + 1)
        hotel_budget *= scale
        meals_budget *= scale
        transit_budget *= scale
        tickets_budget = 0

    return {
        "intercity": round(intercity_cost, 1),
        "hotel": round(hotel_budget, 1),
        "meals": round(meals_budget, 1),
        "transit": round(transit_budget, 1),
        "tickets": round(tickets_budget, 1),
        "target_total": round(tier_budget, 1),
    }
