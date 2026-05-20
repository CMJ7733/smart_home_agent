from langchain_core.tools import tool
from app.tools.iotda_client import IotdaClient, IotdaError
from app.tools.device_registry import DeviceRegistry, DeviceNotFoundError
from app.core.config import get_settings

_client: IotdaClient | None = None
_registry: DeviceRegistry | None = None


def _get_client() -> IotdaClient:
    global _client
    if _client is None:
        s = get_settings()
        _client = IotdaClient(s.iotda_endpoint, s.iotda_project_id, s.iotda_ak, s.iotda_sk)
    return _client


def _get_registry() -> DeviceRegistry:
    global _registry
    if _registry is None:
        _registry = DeviceRegistry()
    return _registry


@tool(description="设置指定房间的温度，room: 房间名，value: 目标温度（摄氏度）")
def set_temperature(room: str, value: int) -> str:
    try:
        device = _get_registry().lookup(room, "ac")
        _get_client().send_sync_command(
            device["device_id"], "ACControl", "SetTemperature",
            {"temperature": value, "on": True},
        )
        return f"{room}空调已设置为 {value}°C"
    except DeviceNotFoundError as e:
        return f"设备未找到: {e}"
    except IotdaError as e:
        return f"设备调用失败: {e}"


@tool(description="控制指定房间的灯光，room: 房间名，on: True开/False关，color: 颜色，brightness: 亮度0-100")
def toggle_light(room: str, on: bool, color: str = "白色", brightness: int = 80) -> str:
    try:
        device = _get_registry().lookup(room, "light")
        _get_client().send_sync_command(
            device["device_id"], "LightControl", "SetLight",
            {"on": on, "color": color, "brightness": brightness},
        )
        status = "打开" if on else "关闭"
        return f"{room}灯已{status}，亮度={brightness}，颜色={color}"
    except DeviceNotFoundError as e:
        return f"设备未找到: {e}"
    except IotdaError as e:
        return f"设备调用失败: {e}"


@tool(description="控制指定房间的窗帘，room: 房间名，action: open/close/stop")
def control_curtain(room: str, action: str) -> str:
    try:
        device = _get_registry().lookup(room, "curtain")
        _get_client().send_sync_command(
            device["device_id"], "CurtainControl", "SetCurtain",
            {"action": action},
        )
        action_zh = {"open": "打开", "close": "关闭", "stop": "停止"}.get(action, action)
        return f"{room}窗帘已{action_zh}"
    except DeviceNotFoundError as e:
        return f"设备未找到: {e}"
    except IotdaError as e:
        return f"设备调用失败: {e}"


@tool(description="启动指定区域的扫地机器人，room: 区域名（留空表示全屋）")
def start_robot_vacuum(room: str = "") -> str:
    try:
        device = _get_registry().lookup("全屋", "vacuum")
        _get_client().send_sync_command(
            device["device_id"], "VacuumControl", "StartVacuum",
            {"room": room or "全屋"},
        )
        return f"扫地机器人已启动{'（' + room + '区域）' if room else '（全屋）'}"
    except DeviceNotFoundError as e:
        return f"设备未找到: {e}"
    except IotdaError as e:
        return f"设备调用失败: {e}"


@tool(description="查询指定设备的当前状态，device_id: 设备唯一标识")
def query_device_status(device_id: str) -> str:
    try:
        shadow = _get_client().get_device_shadow(device_id)
        shadow_items = shadow.get("shadow", [])
        if not shadow_items:
            return f"设备 {device_id} 无状态数据"
        reported = shadow_items[0].get("reported", {}).get("properties", {})
        return f"设备 {device_id} 当前状态: {reported}"
    except IotdaError as e:
        return f"状态查询失败: {e}"
