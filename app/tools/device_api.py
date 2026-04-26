# TODO (Phase 1): 智能家居设备控制模拟接口
# 所有函数均为 mock，返回模拟成功响应，供 LangGraph tool_caller_node 调用
# Phase 2+: 可对接真实智能家居 API（米家/涂鸦/Home Assistant）

from langchain_core.tools import tool


@tool(description="设置指定房间的温度，room: 房间名，value: 目标温度（摄氏度）")
def set_temperature(room: str, value: int) -> str:
    raise NotImplementedError("Phase 1: 待实现")


@tool(description="控制指定房间的灯光，room: 房间名，on: True开/False关，color: 颜色，brightness: 亮度0-100")
def toggle_light(room: str, on: bool, color: str = "白色", brightness: int = 80) -> str:
    raise NotImplementedError("Phase 1: 待实现")


@tool(description="控制指定房间的窗帘，room: 房间名，action: open/close/stop")
def control_curtain(room: str, action: str) -> str:
    raise NotImplementedError("Phase 1: 待实现")


@tool(description="启动指定区域的扫地机器人，room: 区域名（留空表示全屋）")
def start_robot_vacuum(room: str = "") -> str:
    raise NotImplementedError("Phase 1: 待实现")


@tool(description="查询指定设备的当前状态，device_id: 设备唯一标识")
def query_device_status(device_id: str) -> str:
    raise NotImplementedError("Phase 1: 待实现")
