# 迁移自 agent/tools/agent_tools.py → get_weather
# Phase 1: mock 实现，后续可对接真实天气 API

from langchain_core.tools import tool


@tool(description="获取指定城市的天气，以消息字符串的形式返回")
def get_weather(city: str) -> str:
    return f"城市{city}天气为晴天，气温26摄氏度，空气湿度50%，南风1级，AQI21，最近6小时降雨概率极低"
