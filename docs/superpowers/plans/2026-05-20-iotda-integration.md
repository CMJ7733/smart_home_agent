# IoTDA 接入实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 `app/tools/device_api.py` 中全为 `NotImplementedError` 的设备控制工具替换为华为云 IoTDA 同步命令下发，并用一个独立 Python 进程（MQTT 模拟器）代替真实硬件，实现端到端的云端真实往返。

**Architecture:** Agent 调 `IotdaClient.send_sync_command()` → IoTDA REST → MQTT → `DeviceSimulator` → 属性上报 → IoTDA 设备影子。`DeviceRegistry` 维护 room+type → device_id/secret 的静态映射，由 `iotda_provision.py` 一键生成。

**Tech Stack:** `huaweicloudsdkiotda`（应用侧 REST）、`paho-mqtt`（设备侧 MQTT）、`PyYAML`（已在 requirements.txt）

---

## 文件地图

| 操作 | 路径 | 职责 |
|---|---|---|
| 新建 | `app/tools/device_registry.py` | room+type → device_id/secret 查表 |
| 新建 | `app/tools/iotda_client.py` | IAM 鉴权、同步命令、设备影子 |
| 新建 | `scripts/device_simulator.py` | 7 个虚拟设备的 MQTT 连接与状态机 |
| 新建 | `scripts/iotda_provision.py` | 一键建产品+设备，生成 iotda_devices.yml |
| 新建(自动) | `config/iotda_devices.yml` | provision 脚本输出，运行时读取 |
| 新建 | `tests/test_device_registry.py` | DeviceRegistry 单元测试 |
| 新建 | `tests/test_iotda_client.py` | IotdaClient 单元测试 |
| 修改 | `app/core/config.py` | 新增 4 个 IoTDA 字段 |
| 修改 | `.env.example` | 新增 4 个占位字段 |
| 修改 | `requirements.txt` | 新增 `huaweicloudsdkiotda`、`paho-mqtt` |
| 修改 | `app/tools/device_api.py` | 5 个 @tool 函数接入 IoTDA |
| 修改 | `app/agent/nodes/tool_caller.py` | 扩展以执行 scene_planner 返回的动作列表 |
| 新建 | `tests/test_device_api.py` | device_api @tool 函数单元测试 |
| 新建 | `tests/test_tool_caller.py` | tool_caller_node 场景路径单元测试 |

---

## Task 1: 依赖与配置

**Files:**
- Modify: `requirements.txt`
- Modify: `app/core/config.py`
- Modify: `.env.example`

- [ ] **Step 1: 添加依赖**

在 `requirements.txt` 末尾追加：
```
huaweicloudsdkiotda>=3.1.0
paho-mqtt>=2.0.0
```

- [ ] **Step 2: 新增 IoTDA 配置字段**

在 `app/core/config.py` 的 `Settings` 类中（在 `eval_db_path` 字段后）添加：

```python
    # Huawei IoTDA (Phase IoTDA)
    iotda_endpoint: str = ""          # e.g. "xxxxxx.iotda.cn-north-4.myhuaweicloud.com" (无 https://)
    iotda_project_id: str = ""
    iotda_ak: str = ""
    iotda_sk: str = ""
```

- [ ] **Step 3: 更新 .env.example**

在 `.env.example` 末尾追加：
```
# Huawei IoTDA
IOTDA_ENDPOINT=xxxxxx.iotda.cn-north-4.myhuaweicloud.com
IOTDA_PROJECT_ID=your-project-id
IOTDA_AK=your-ak
IOTDA_SK=your-sk
```

- [ ] **Step 4: 验证导入**

```bash
pip install huaweicloudsdkiotda paho-mqtt
python -c "from huaweicloudsdkiotda.v5 import IoTDAClient; from huaweicloudsdkcore.auth.credentials import BasicCredentials; import paho.mqtt.client as mqtt; print('OK')"
```

期望输出：`OK`

- [ ] **Step 5: 提交**

```bash
git add requirements.txt app/core/config.py .env.example
git commit -m "feat(iotda): add dependencies and config fields"
```

---

## Task 2: DeviceRegistry

**Files:**
- Create: `app/tools/device_registry.py`
- Create: `tests/test_device_registry.py`

- [ ] **Step 1: 写失败测试**

新建 `tests/test_device_registry.py`：

```python
import pytest
import yaml
from pathlib import Path
from app.tools.device_registry import DeviceRegistry, DeviceNotFoundError


@pytest.fixture
def registry_yml(tmp_path: Path) -> Path:
    data = {
        "卧室": {
            "light": {"device_id": "bedroom-light-001", "device_secret": "secret-l1"},
            "ac":    {"device_id": "bedroom-ac-001",    "device_secret": "secret-a1"},
        },
        "全屋": {
            "vacuum": {"device_id": "home-vacuum-001", "device_secret": "secret-v1"},
        },
    }
    path = tmp_path / "iotda_devices.yml"
    path.write_text(yaml.dump(data, allow_unicode=True))
    return path


def test_lookup_success(registry_yml):
    reg = DeviceRegistry(registry_yml)
    info = reg.lookup("卧室", "light")
    assert info["device_id"] == "bedroom-light-001"
    assert info["device_secret"] == "secret-l1"


def test_lookup_missing_room(registry_yml):
    reg = DeviceRegistry(registry_yml)
    with pytest.raises(DeviceNotFoundError, match="客厅"):
        reg.lookup("客厅", "light")


def test_lookup_missing_type(registry_yml):
    reg = DeviceRegistry(registry_yml)
    with pytest.raises(DeviceNotFoundError, match="curtain"):
        reg.lookup("卧室", "curtain")


def test_all_devices(registry_yml):
    reg = DeviceRegistry(registry_yml)
    devices = reg.all_devices()
    assert len(devices) == 3
    ids = {d["device_id"] for d in devices}
    assert "home-vacuum-001" in ids


def test_missing_file():
    with pytest.raises(FileNotFoundError, match="iotda_provision"):
        DeviceRegistry(Path("/nonexistent/iotda_devices.yml"))
```

- [ ] **Step 2: 运行确认失败**

```bash
pytest tests/test_device_registry.py -v
```

期望：`ModuleNotFoundError: No module named 'app.tools.device_registry'`

- [ ] **Step 3: 实现 DeviceRegistry**

新建 `app/tools/device_registry.py`：

```python
import yaml
from pathlib import Path

DEVICE_CONFIG_PATH = Path("config/iotda_devices.yml")


class DeviceNotFoundError(Exception):
    pass


class DeviceRegistry:
    def __init__(self, path: Path = DEVICE_CONFIG_PATH):
        if not path.exists():
            raise FileNotFoundError(
                f"Device registry not found at {path}. Run: python scripts/iotda_provision.py"
            )
        with open(path, encoding="utf-8") as f:
            self._devices: dict = yaml.safe_load(f) or {}

    def lookup(self, room: str, device_type: str) -> dict:
        """Returns {"device_id": ..., "device_secret": ...}"""
        room_data = self._devices.get(room)
        if not room_data:
            raise DeviceNotFoundError(f"No devices found for room='{room}'")
        info = room_data.get(device_type)
        if not info:
            raise DeviceNotFoundError(
                f"No device of type='{device_type}' in room='{room}'"
            )
        return info

    def all_devices(self) -> list[dict]:
        """Returns list of all devices with room, type, device_id, device_secret."""
        result = []
        for room, types in self._devices.items():
            for dtype, info in types.items():
                result.append({"room": room, "type": dtype, **info})
        return result
```

- [ ] **Step 4: 运行确认通过**

```bash
pytest tests/test_device_registry.py -v
```

期望：5 个测试全部 PASS

- [ ] **Step 5: 提交**

```bash
git add app/tools/device_registry.py tests/test_device_registry.py
git commit -m "feat(iotda): add DeviceRegistry with room+type lookup"
```

---

## Task 3: IotdaClient

**Files:**
- Create: `app/tools/iotda_client.py`
- Create: `tests/test_iotda_client.py`

- [ ] **Step 1: 写失败测试**

新建 `tests/test_iotda_client.py`：

```python
import pytest
from unittest.mock import MagicMock, patch, call
from huaweicloudsdkcore.exceptions.exceptions import ClientRequestException
from app.tools.iotda_client import IotdaClient, IotdaError


def _make_client(mock_hw_cls):
    """Construct IotdaClient with mocked underlying HW SDK client."""
    return IotdaClient(
        endpoint="test.iotda.cn-north-4.myhuaweicloud.com",
        project_id="proj-123",
        ak="ak",
        sk="sk",
    )


@pytest.fixture
def hw_instance():
    """Returns the mocked SDK client instance."""
    with patch("app.tools.iotda_client._HWClient") as mock_cls:
        instance = MagicMock()
        mock_cls.new_builder.return_value \
            .with_credentials.return_value \
            .with_endpoint.return_value \
            .build.return_value = instance
        yield instance


def test_send_sync_command_success(hw_instance):
    mock_resp = MagicMock()
    mock_resp.to_dict.return_value = {"command_id": "cmd-1", "status": "DELIVERED"}
    hw_instance.create_sync_command.return_value = mock_resp

    client = IotdaClient("ep.com", "proj", "ak", "sk")
    result = client.send_sync_command("dev-1", "LightControl", "SetLight", {"on": True})

    assert result == {"command_id": "cmd-1", "status": "DELIVERED"}
    hw_instance.create_sync_command.assert_called_once()


def test_send_sync_command_4xx_raises_iotda_error(hw_instance):
    exc = ClientRequestException(request_id="r1", status_code=404,
                                  error_code="IOTDA.000404", error_msg="device not found")
    hw_instance.create_sync_command.side_effect = exc

    client = IotdaClient("ep.com", "proj", "ak", "sk")
    with pytest.raises(IotdaError, match="IOTDA.000404"):
        client.send_sync_command("dev-x", "SvcA", "CmdA", {})


def test_send_sync_command_429_retries_once(hw_instance):
    exc_429 = ClientRequestException(request_id="r1", status_code=429,
                                      error_code="APIG.0308", error_msg="throttled")
    ok_resp = MagicMock()
    ok_resp.to_dict.return_value = {"status": "DELIVERED"}
    hw_instance.create_sync_command.side_effect = [exc_429, ok_resp]

    client = IotdaClient("ep.com", "proj", "ak", "sk")
    with patch("app.tools.iotda_client.time.sleep") as mock_sleep:
        result = client.send_sync_command("dev-1", "SvcA", "CmdA", {})

    assert result == {"status": "DELIVERED"}
    mock_sleep.assert_called_once_with(1)
    assert hw_instance.create_sync_command.call_count == 2


def test_send_sync_command_429_twice_raises(hw_instance):
    exc_429 = ClientRequestException(request_id="r1", status_code=429,
                                      error_code="APIG.0308", error_msg="throttled")
    hw_instance.create_sync_command.side_effect = [exc_429, exc_429]

    client = IotdaClient("ep.com", "proj", "ak", "sk")
    with patch("app.tools.iotda_client.time.sleep"):
        with pytest.raises(IotdaError, match="APIG.0308"):
            client.send_sync_command("dev-1", "SvcA", "CmdA", {})


def test_get_device_shadow_success(hw_instance):
    mock_resp = MagicMock()
    mock_resp.to_dict.return_value = {
        "device_id": "dev-1",
        "shadow": [{"service_id": "LightControl",
                    "reported": {"properties": {"on": True, "brightness": 80}}}],
    }
    hw_instance.show_device_shadow.return_value = mock_resp

    client = IotdaClient("ep.com", "proj", "ak", "sk")
    result = client.get_device_shadow("dev-1")

    assert result["shadow"][0]["reported"]["properties"]["on"] is True


def test_get_device_shadow_error(hw_instance):
    exc = ClientRequestException(request_id="r1", status_code=404,
                                  error_code="IOTDA.000404", error_msg="not found")
    hw_instance.show_device_shadow.side_effect = exc

    client = IotdaClient("ep.com", "proj", "ak", "sk")
    with pytest.raises(IotdaError, match="IOTDA.000404"):
        client.get_device_shadow("dev-x")
```

- [ ] **Step 2: 运行确认失败**

```bash
pytest tests/test_iotda_client.py -v
```

期望：`ModuleNotFoundError: No module named 'app.tools.iotda_client'`

- [ ] **Step 3: 实现 IotdaClient**

新建 `app/tools/iotda_client.py`：

```python
import time
from huaweicloudsdkcore.auth.credentials import BasicCredentials
from huaweicloudsdkcore.exceptions.exceptions import ClientRequestException
from huaweicloudsdkiotda.v5 import IoTDAClient as _HWClient
from huaweicloudsdkiotda.v5.model import (
    CreateSyncCommandRequest,
    SyncDeviceCommand,
    ShowDeviceShadowRequest,
)


class IotdaError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"IoTDA [{code}]: {message}")


class IotdaClient:
    def __init__(self, endpoint: str, project_id: str, ak: str, sk: str):
        self._project_id = project_id
        credentials = BasicCredentials(ak, sk, project_id)
        self._client = (
            _HWClient.new_builder()
            .with_credentials(credentials)
            .with_endpoint(f"https://{endpoint}")
            .build()
        )

    def send_sync_command(
        self, device_id: str, service_id: str, command_name: str, params: dict
    ) -> dict:
        request = CreateSyncCommandRequest(device_id=device_id)
        request.body = SyncDeviceCommand(
            service_id=service_id,
            command_name=command_name,
            paras=params,
        )
        try:
            return self._client.create_sync_command(request).to_dict()
        except ClientRequestException as e:
            if e.status_code == 429:
                time.sleep(1)
                try:
                    return self._client.create_sync_command(request).to_dict()
                except ClientRequestException as e2:
                    raise IotdaError(e2.error_code, e2.error_msg) from e2
            raise IotdaError(e.error_code, e.error_msg) from e

    def get_device_shadow(self, device_id: str) -> dict:
        request = ShowDeviceShadowRequest(device_id=device_id)
        try:
            return self._client.show_device_shadow(request).to_dict()
        except ClientRequestException as e:
            raise IotdaError(e.error_code, e.error_msg) from e
```

- [ ] **Step 4: 运行确认通过**

```bash
pytest tests/test_iotda_client.py -v
```

期望：6 个测试全部 PASS

- [ ] **Step 5: 验证 SDK 类名正确**

若 Step 4 报 `ImportError`（类名不对），运行以下命令找到正确类名：

```bash
python -c "import huaweicloudsdkiotda.v5.model as m; print([x for x in dir(m) if 'sync' in x.lower() or 'command' in x.lower() or 'shadow' in x.lower()])"
```

根据输出把 `SyncDeviceCommand` / `CreateSyncCommandRequest` / `ShowDeviceShadowRequest` 替换为实际类名，再重跑测试。

- [ ] **Step 6: 提交**

```bash
git add app/tools/iotda_client.py tests/test_iotda_client.py
git commit -m "feat(iotda): add IotdaClient with sync command and device shadow"
```

---

## Task 4: 改造 device_api.py

**Files:**
- Modify: `app/tools/device_api.py`
- Create: `tests/test_device_api.py`

- [ ] **Step 1: 写失败测试**

新建 `tests/test_device_api.py`：

```python
import pytest
from unittest.mock import MagicMock, patch


def _mock_env(monkeypatch, tmp_path):
    import yaml
    data = {
        "卧室": {
            "light": {"device_id": "bedroom-light-001", "device_secret": "sec"},
            "ac":    {"device_id": "bedroom-ac-001",    "device_secret": "sec"},
            "curtain": {"device_id": "bedroom-curtain-001", "device_secret": "sec"},
        },
        "全屋": {
            "vacuum": {"device_id": "home-vacuum-001", "device_secret": "sec"},
        },
    }
    yml = tmp_path / "iotda_devices.yml"
    yml.write_text(yaml.dump(data, allow_unicode=True))
    return yml


@pytest.fixture(autouse=True)
def reset_module_singletons():
    import app.tools.device_api as m
    m._client = None
    m._registry = None
    yield
    m._client = None
    m._registry = None


def _patched_client():
    mock_client = MagicMock()
    mock_client.send_sync_command.return_value = {"status": "DELIVERED"}
    mock_client.get_device_shadow.return_value = {
        "shadow": [{"reported": {"properties": {"on": True}}}]
    }
    return mock_client


def test_toggle_light_on(tmp_path, monkeypatch):
    yml = _mock_env(monkeypatch, tmp_path)
    mock_client = _patched_client()
    with patch("app.tools.device_api._get_client", return_value=mock_client), \
         patch("app.tools.device_api.DeviceRegistry") as mock_reg_cls:
        mock_reg_cls.return_value.lookup.return_value = {
            "device_id": "bedroom-light-001", "device_secret": "sec"
        }
        from app.tools.device_api import toggle_light
        result = toggle_light.invoke({"room": "卧室", "on": True})

    assert "打开" in result
    mock_client.send_sync_command.assert_called_once_with(
        "bedroom-light-001", "LightControl", "SetLight",
        {"on": True, "color": "白色", "brightness": 80},
    )


def test_set_temperature(tmp_path, monkeypatch):
    _mock_env(monkeypatch, tmp_path)
    mock_client = _patched_client()
    with patch("app.tools.device_api._get_client", return_value=mock_client), \
         patch("app.tools.device_api.DeviceRegistry") as mock_reg_cls:
        mock_reg_cls.return_value.lookup.return_value = {
            "device_id": "bedroom-ac-001", "device_secret": "sec"
        }
        from app.tools.device_api import set_temperature
        result = set_temperature.invoke({"room": "卧室", "value": 26})

    assert "26" in result
    mock_client.send_sync_command.assert_called_once_with(
        "bedroom-ac-001", "ACControl", "SetTemperature",
        {"temperature": 26, "on": True},
    )


def test_iotda_error_returned_as_string(tmp_path, monkeypatch):
    _mock_env(monkeypatch, tmp_path)
    from app.tools.iotda_client import IotdaError
    mock_client = MagicMock()
    mock_client.send_sync_command.side_effect = IotdaError("IOTDA.014011", "device not online")
    with patch("app.tools.device_api._get_client", return_value=mock_client), \
         patch("app.tools.device_api.DeviceRegistry") as mock_reg_cls:
        mock_reg_cls.return_value.lookup.return_value = {
            "device_id": "bedroom-light-001", "device_secret": "sec"
        }
        from app.tools.device_api import toggle_light
        result = toggle_light.invoke({"room": "卧室", "on": True})

    assert "设备调用失败" in result
    assert "IOTDA.014011" in result
```

- [ ] **Step 2: 运行确认失败**

```bash
pytest tests/test_device_api.py -v
```

期望：`ImportError` 或测试因 `NotImplementedError` 失败

- [ ] **Step 3: 完整替换 device_api.py**

用以下内容完整覆盖 `app/tools/device_api.py`：

```python
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
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/test_device_api.py -v
```

期望：3 个测试全部 PASS

- [ ] **Step 5: 提交**

```bash
git add app/tools/device_api.py tests/test_device_api.py
git commit -m "feat(iotda): rewire device_api tools to IoTDA sync commands"
```

---

## Task 5: 扩展 tool_caller_node 以支持场景执行

**Files:**
- Modify: `app/agent/nodes/tool_caller.py`
- Create: `tests/test_tool_caller.py`

**背景：** `scene_planner_node` 返回 `{"tool_calls": [{"tool": "toggle_light", "args": {...}}, ...]}` 这样的动作列表，但当前 `tool_caller_node` 只读 `extracted_entities`，场景路径无法执行。需要扩展 tool_caller_node 检测到动作列表时顺序执行。

- [ ] **Step 1: 写失败测试**

新建 `tests/test_tool_caller.py`：

```python
import pytest
from unittest.mock import MagicMock, patch
from app.agent.nodes.tool_caller import tool_caller_node


def test_scene_path_executes_action_list():
    """tool_caller_node executes pre-populated scene action list from scene_planner."""
    state = {
        "tool_calls": [
            {"tool": "toggle_light", "args": {"room": "卧室", "on": False}},
        ],
        "extracted_entities": {},
    }
    with patch("app.agent.nodes.tool_caller.toggle_light") as mock_tool:
        mock_tool.invoke.return_value = "卧室灯已关闭"
        result = tool_caller_node(state)

    assert len(result["tool_calls"]) == 1
    assert result["tool_calls"][0]["action"] == "toggle_light"
    assert "关闭" in result["tool_calls"][0]["result"]
    mock_tool.invoke.assert_called_once_with({"room": "卧室", "on": False})


def test_scene_path_unknown_tool_returns_error():
    state = {
        "tool_calls": [{"tool": "unknown_tool", "args": {}}],
        "extracted_entities": {},
    }
    result = tool_caller_node(state)
    assert "未知工具" in result["tool_calls"][0]["result"]


def test_device_control_path_unrecognized_device():
    """Empty tool_calls + extracted_entities → device control path."""
    state = {
        "tool_calls": [],
        "extracted_entities": {"device": "冰箱", "room": "厨房", "action": "开", "value": ""},
    }
    result = tool_caller_node(state)
    assert len(result["tool_calls"]) == 1
    assert "未识别设备" in result["tool_calls"][0]["result"]
```

- [ ] **Step 2: 运行确认失败**

```bash
pytest tests/test_tool_caller.py -v
```

期望：`test_scene_path_executes_action_list` FAIL（当前 tool_caller_node 不处理 scene 路径）

- [ ] **Step 3: 用以下内容完整替换 tool_caller.py**

```python
from app.agent.state import AgentState
from app.tools.device_api import (
    set_temperature, toggle_light, control_curtain, start_robot_vacuum,
)

_TOOL_MAP = {
    "toggle_light": toggle_light,
    "set_temperature": set_temperature,
    "control_curtain": control_curtain,
    "start_robot_vacuum": start_robot_vacuum,
}


def _execute_scene_actions(actions: list[dict]) -> dict:
    """Execute a pre-planned list of tool actions from scene_planner_node."""
    results = []
    for action in actions:
        tool_name = action.get("tool", "")
        args = action.get("args", {})
        tool_fn = _TOOL_MAP.get(tool_name)
        if not tool_fn:
            results.append({"action": tool_name, "args": args, "result": f"未知工具: {tool_name}"})
            continue
        try:
            result = tool_fn.invoke(args)
            results.append({"action": tool_name, "args": args, "result": str(result)})
        except Exception as e:
            results.append({"action": tool_name, "args": args, "result": f"执行失败: {e}"})
    return {"tool_calls": results}


def tool_caller_node(state: AgentState) -> AgentState:
    """设备工具调用节点: 根据 extracted_entities 调用对应设备 API，或执行 scene_planner 的动作列表"""
    existing = state.get("tool_calls", [])
    if existing and isinstance(existing[0], dict) and "tool" in existing[0]:
        return _execute_scene_actions(existing)

    entities = state.get("extracted_entities", {})
    device = entities.get("device", "")
    room = entities.get("room", "")
    action = entities.get("action", "")
    value = entities.get("value", "")

    tool_calls = []
    try:
        if device in ("灯", "灯光", "灯具"):
            on = action in ("开", "打开", "开启")
            result = toggle_light.invoke({"room": room, "on": on})
        elif device in ("空调", "温度"):
            result = set_temperature.invoke({"room": room, "value": int(value or 24)})
        elif device == "窗帘":
            act = "open" if action in ("开", "打开") else "close"
            result = control_curtain.invoke({"room": room, "action": act})
        elif device in ("扫地机", "扫地机器人"):
            result = start_robot_vacuum.invoke({"room": room})
        else:
            result = f"未识别设备: {device}"
        tool_calls.append({"action": action, "device": device, "args": entities, "result": str(result)})
    except Exception as e:
        tool_calls.append({"action": action, "device": device, "args": entities, "result": f"执行失败: {e}"})

    return {"tool_calls": tool_calls}
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/test_tool_caller.py -v
```

期望：3 个测试全部 PASS

- [ ] **Step 5: 提交**

```bash
git add app/agent/nodes/tool_caller.py tests/test_tool_caller.py
git commit -m "feat(iotda): extend tool_caller_node to execute scene action lists"
```

---

## Task 6: DeviceSimulator 基类

**Files:**
- Create: `scripts/device_simulator.py`（基类部分）

- [ ] **Step 1: 新建 scripts/device_simulator.py（基类）**

```python
"""
Huawei IoTDA Device Simulator
Runs 7 virtual devices over MQTT TLS, receiving sync commands and reporting properties.

Usage:
    python scripts/device_simulator.py

Requires:
    - config/iotda_devices.yml (generated by scripts/iotda_provision.py)
    - .env with IOTDA_ENDPOINT, IOTDA_AK, IOTDA_SK, IOTDA_PROJECT_ID
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import ssl
import threading
import time
from pathlib import Path

import paho.mqtt.client as mqtt
import yaml

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

DEVICE_CONFIG_PATH = Path("config/iotda_devices.yml")


def _mqtt_password(device_secret: str, client_id: str) -> str:
    """HMAC-SHA256(device_secret, client_id) as hex — IoTDA MQTT auth formula."""
    return hmac.new(
        device_secret.encode(),
        client_id.encode(),
        hashlib.sha256,
    ).hexdigest()


class DeviceSimulator:
    """Base class for a virtual IoTDA device connected over MQTT TLS."""

    SERVICE_ID: str = ""       # override in subclass
    COMMAND_NAME: str = ""     # override in subclass

    def __init__(
        self,
        device_id: str,
        device_secret: str,
        endpoint: str,
        room: str = "",
        device_type: str = "",
    ):
        self.device_id = device_id
        self.room = room
        self.device_type = device_type
        self._endpoint = endpoint
        self._logger = logging.getLogger(f"[{room}-{device_type}]")
        self._state: dict = {}

        timestamp = str(int(time.time()))
        client_id = f"{device_id}_0_0_{timestamp}"
        password = _mqtt_password(device_secret, client_id)

        self._mqtt = mqtt.Client(
            client_id=client_id,
            protocol=mqtt.MQTTv311,
            reconnect_on_failure=True,
        )
        self._mqtt.username_pw_set(username=device_id, password=password)
        self._mqtt.tls_set(cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS)
        self._mqtt.on_connect = self._on_connect
        self._mqtt.on_disconnect = self._on_disconnect
        self._mqtt.on_message = self._on_message

    # ── MQTT lifecycle ──────────────────────────────────────────────────────

    def connect(self):
        self._mqtt.connect(host=self._endpoint, port=8883, keepalive=60)
        self._mqtt.loop_start()

    def disconnect(self):
        self._mqtt.loop_stop()
        self._mqtt.disconnect()

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            topic = f"$oc/devices/{self.device_id}/sys/commands/#"
            client.subscribe(topic, qos=1)
            self._logger.info(f"Connected, subscribed to {topic}")
            self._report_properties()
        else:
            self._logger.warning(f"Connection failed rc={rc}")

    def _on_disconnect(self, client, userdata, rc):
        self._logger.warning(f"Disconnected rc={rc}, will retry...")

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
        except json.JSONDecodeError:
            self._logger.error(f"Invalid JSON: {msg.payload}")
            return

        command_id = payload.get("command_id", "")
        command_name = payload.get("command_name", "")
        paras = payload.get("paras", {})

        self._logger.info(f"Command received: {command_name} {paras}")

        if command_name == self.COMMAND_NAME:
            self.handle_command(paras)
        else:
            self._logger.warning(f"Unknown command: {command_name}")

        self._send_command_response(command_id, command_name)
        self._report_properties()

    # ── Override in subclasses ──────────────────────────────────────────────

    def handle_command(self, paras: dict):
        """Update internal state from command parameters."""
        raise NotImplementedError

    # ── Internal helpers ────────────────────────────────────────────────────

    def _report_properties(self):
        topic = f"$oc/devices/{self.device_id}/sys/properties/report"
        payload = {
            "services": [{
                "service_id": self.SERVICE_ID,
                "properties": self._state,
                "event_time": time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()),
            }]
        }
        self._mqtt.publish(topic, json.dumps(payload), qos=1)
        self._logger.info(f"Properties reported: {self._state}")

    def _send_command_response(self, command_id: str, command_name: str):
        if not command_id:
            return
        topic = f"$oc/devices/{self.device_id}/sys/commands/{command_id}/response"
        payload = {
            "result_code": 0,
            "response_name": f"{command_name}Response",
            "paras": {"result": "success"},
        }
        self._mqtt.publish(topic, json.dumps(payload), qos=1)
```

- [ ] **Step 2: 验证基类语法**

```bash
python -c "import sys; sys.path.insert(0, '.'); from scripts.device_simulator import DeviceSimulator; print('Base OK')"
```

期望：`Base OK`

---

## Task 7: 各设备子类 + main()

**Files:**
- Modify: `scripts/device_simulator.py`（追加子类和 main）

- [ ] **Step 1: 在 device_simulator.py 末尾追加 4 个子类**

```python
# ── Device subclasses ───────────────────────────────────────────────────────

class LightSimulator(DeviceSimulator):
    SERVICE_ID = "LightControl"
    COMMAND_NAME = "SetLight"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._state = {"on": False, "color": "白色", "brightness": 0}

    def handle_command(self, paras: dict):
        self._state["on"] = bool(paras.get("on", False))
        self._state["color"] = paras.get("color", self._state["color"])
        self._state["brightness"] = int(paras.get("brightness", self._state["brightness"]))


class ACSimulator(DeviceSimulator):
    SERVICE_ID = "ACControl"
    COMMAND_NAME = "SetTemperature"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._state = {"on": False, "temperature": 26}

    def handle_command(self, paras: dict):
        self._state["on"] = bool(paras.get("on", True))
        self._state["temperature"] = int(paras.get("temperature", self._state["temperature"]))


class CurtainSimulator(DeviceSimulator):
    SERVICE_ID = "CurtainControl"
    COMMAND_NAME = "SetCurtain"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._state = {"position": "closed"}

    def handle_command(self, paras: dict):
        action = paras.get("action", "stop")
        self._state["position"] = {"open": "open", "close": "closed", "stop": "stopped"}.get(
            action, "stopped"
        )


class VacuumSimulator(DeviceSimulator):
    SERVICE_ID = "VacuumControl"
    COMMAND_NAME = "StartVacuum"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._state = {"status": "idle", "room": ""}

    def handle_command(self, paras: dict):
        self._state["status"] = "working"
        self._state["room"] = paras.get("room", "全屋")
```

- [ ] **Step 2: 在 device_simulator.py 末尾追加 main()**

```python
# ── Entry point ─────────────────────────────────────────────────────────────

_SIMULATOR_MAP: dict[str, type[DeviceSimulator]] = {
    "light": LightSimulator,
    "ac": ACSimulator,
    "curtain": CurtainSimulator,
    "vacuum": VacuumSimulator,
}


def main():
    import os
    from dotenv import load_dotenv
    load_dotenv()

    endpoint = os.environ["IOTDA_ENDPOINT"]

    with open(DEVICE_CONFIG_PATH, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    simulators: list[DeviceSimulator] = []
    for room, types in config.items():
        for dtype, info in types.items():
            cls = _SIMULATOR_MAP.get(dtype)
            if not cls:
                continue
            sim = cls(
                device_id=info["device_id"],
                device_secret=info["device_secret"],
                endpoint=endpoint,
                room=room,
                device_type=dtype,
            )
            simulators.append(sim)

    logging.info(f"Starting {len(simulators)} device simulators...")
    for sim in simulators:
        sim.connect()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Shutting down simulators...")
        for sim in simulators:
            sim.disconnect()


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: 验证语法**

```bash
python -c "
import sys; sys.path.insert(0, '.')
from scripts.device_simulator import LightSimulator, ACSimulator, CurtainSimulator, VacuumSimulator, main
print('All simulator classes OK')
"
```

期望：`All simulator classes OK`

- [ ] **Step 4: 提交**

```bash
git add scripts/device_simulator.py
git commit -m "feat(iotda): add device simulator with 4 device types and MQTT TLS"
```

---

## Task 8: Provision 脚本

**Files:**
- Create: `scripts/iotda_provision.py`

- [ ] **Step 1: 新建 scripts/iotda_provision.py**

```python
"""
IoTDA Provision Script
Creates 4 products and 7 devices in Huawei IoTDA, writes config/iotda_devices.yml.

Usage:
    python scripts/iotda_provision.py

Requires: .env with IOTDA_ENDPOINT, IOTDA_PROJECT_ID, IOTDA_AK, IOTDA_SK
"""

import os
import yaml
from pathlib import Path
from dotenv import load_dotenv
from huaweicloudsdkcore.auth.credentials import BasicCredentials
from huaweicloudsdkiotda.v5 import IoTDAClient
from huaweicloudsdkiotda.v5.model import (
    CreateProductRequest,
    CreateProductRequestBody,
    ServiceCapability,
    ServiceCommand,
    ServiceCommandPara,
    ServiceProperty,
    CreateDeviceRequest,
    AddDevice,
)

load_dotenv()

ENDPOINT = os.environ["IOTDA_ENDPOINT"]
PROJECT_ID = os.environ["IOTDA_PROJECT_ID"]
AK = os.environ["IOTDA_AK"]
SK = os.environ["IOTDA_SK"]
OUTPUT_PATH = Path("config/iotda_devices.yml")

# ── Product definitions ─────────────────────────────────────────────────────

PRODUCTS = [
    {
        "name": "SmartLight",
        "device_type": "SmartLight",
        "service_id": "LightControl",
        "properties": [
            {"name": "on", "data_type": "bool", "access": "RW"},
            {"name": "color", "data_type": "string", "access": "RW"},
            {"name": "brightness", "data_type": "int", "min": 0, "max": 100, "access": "RW"},
        ],
        "command": {"name": "SetLight", "paras": [
            {"name": "on", "data_type": "bool"},
            {"name": "color", "data_type": "string"},
            {"name": "brightness", "data_type": "int"},
        ]},
    },
    {
        "name": "SmartAC",
        "device_type": "SmartAC",
        "service_id": "ACControl",
        "properties": [
            {"name": "on", "data_type": "bool", "access": "RW"},
            {"name": "temperature", "data_type": "int", "min": 16, "max": 30, "access": "RW"},
        ],
        "command": {"name": "SetTemperature", "paras": [
            {"name": "on", "data_type": "bool"},
            {"name": "temperature", "data_type": "int"},
        ]},
    },
    {
        "name": "SmartCurtain",
        "device_type": "SmartCurtain",
        "service_id": "CurtainControl",
        "properties": [
            {"name": "position", "data_type": "string", "access": "RW"},
        ],
        "command": {"name": "SetCurtain", "paras": [
            {"name": "action", "data_type": "string"},
        ]},
    },
    {
        "name": "RobotVacuum",
        "device_type": "RobotVacuum",
        "service_id": "VacuumControl",
        "properties": [
            {"name": "status", "data_type": "string", "access": "RW"},
            {"name": "room", "data_type": "string", "access": "RW"},
        ],
        "command": {"name": "StartVacuum", "paras": [
            {"name": "room", "data_type": "string"},
        ]},
    },
]

# ── Device layout ───────────────────────────────────────────────────────────

DEVICE_LAYOUT = [
    {"room": "卧室", "type": "light",   "product": "SmartLight",   "name": "bedroom-light"},
    {"room": "卧室", "type": "ac",      "product": "SmartAC",      "name": "bedroom-ac"},
    {"room": "卧室", "type": "curtain", "product": "SmartCurtain", "name": "bedroom-curtain"},
    {"room": "客厅", "type": "light",   "product": "SmartLight",   "name": "livingroom-light"},
    {"room": "客厅", "type": "ac",      "product": "SmartAC",      "name": "livingroom-ac"},
    {"room": "客厅", "type": "curtain", "product": "SmartCurtain", "name": "livingroom-curtain"},
    {"room": "全屋", "type": "vacuum",  "product": "RobotVacuum",  "name": "home-vacuum"},
]


def _build_service(prod: dict) -> ServiceCapability:
    props = [
        ServiceProperty(
            property_name=p["name"],
            data_type=p["data_type"],
            access=p.get("access", "RW"),
            min=str(p["min"]) if "min" in p else None,
            max=str(p["max"]) if "max" in p else None,
        )
        for p in prod["properties"]
    ]
    cmd_paras = [
        ServiceCommandPara(para_name=p["name"], data_type=p["data_type"])
        for p in prod["command"]["paras"]
    ]
    cmd = ServiceCommand(command_name=prod["command"]["name"], paras=cmd_paras)
    return ServiceCapability(
        service_id=prod["service_id"],
        service_type=prod["service_id"],
        properties=props,
        commands=[cmd],
    )


def main():
    credentials = BasicCredentials(AK, SK, PROJECT_ID)
    client = (
        IoTDAClient.new_builder()
        .with_credentials(credentials)
        .with_endpoint(f"https://{ENDPOINT}")
        .build()
    )

    # Step 1: Create products
    product_ids: dict[str, str] = {}
    for prod in PRODUCTS:
        req = CreateProductRequest()
        req.body = CreateProductRequestBody(
            name=prod["name"],
            device_type=prod["device_type"],
            protocol_type="MQTT",
            data_format="json",
            manufacturer_name="Simulator",
            service_capabilities=[_build_service(prod)],
        )
        resp = client.create_product(req)
        product_ids[prod["name"]] = resp.product_id
        print(f"  Created product: {prod['name']} → {resp.product_id}")

    # Step 2: Create devices
    registry: dict = {}
    for layout in DEVICE_LAYOUT:
        product_id = product_ids[layout["product"]]
        req = CreateDeviceRequest()
        req.body = AddDevice(
            device_name=layout["name"],
            node_id=layout["name"],
            product_id=product_id,
        )
        resp = client.create_device(req)
        room = layout["room"]
        dtype = layout["type"]
        registry.setdefault(room, {})[dtype] = {
            "device_id": resp.device_id,
            "device_secret": resp.auth_info.secret,
        }
        print(f"  Created device: {layout['name']} (room={room}, type={dtype}) → {resp.device_id}")

    # Step 3: Write config/iotda_devices.yml
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        yaml.dump(registry, f, allow_unicode=True, default_flow_style=False)
    print(f"\nWritten to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 验证脚本语法（不执行）**

```bash
python -m py_compile scripts/iotda_provision.py && echo "Syntax OK"
```

期望：`Syntax OK`

若报 ImportError（SDK model 类名不对），运行以下命令找到正确类名：

```bash
python -c "import huaweicloudsdkiotda.v5.model as m; print([x for x in dir(m) if 'product' in x.lower() or 'device' in x.lower() or 'service' in x.lower()])"
```

- [ ] **Step 3: 提交**

```bash
git add scripts/iotda_provision.py
git commit -m "feat(iotda): add provision script to create products and devices"
```

---

## Task 9: 端到端冒烟测试

这是手动验证步骤，需要真实 IoTDA 凭证。

- [ ] **Step 1: 开通 IoTDA 试用实例**

登录 [华为云控制台](https://console.huaweicloud.com) → 搜索"IoTDA" → 开通免费试用版 → 记录：
- 实例接入点（Endpoint）
- 项目 ID（Project ID）

- [ ] **Step 2: 创建 IAM 访问密钥（AK/SK）**

控制台右上角 → 我的凭证 → 访问密钥 → 新增访问密钥 → 下载 CSV → 填入 `.env`：

```
IOTDA_ENDPOINT=<你的接入点，不含 https://>
IOTDA_PROJECT_ID=<项目 ID>
IOTDA_AK=<AK>
IOTDA_SK=<SK>
```

- [ ] **Step 3: 运行 provision 脚本**

```bash
python scripts/iotda_provision.py
```

期望输出（示例）：
```
  Created product: SmartLight → 5e5...
  Created product: SmartAC → 6f8...
  ...
  Created device: bedroom-light → 3a2...
  ...
Written to config/iotda_devices.yml
```

检查生成文件：`cat config/iotda_devices.yml`（应有 7 个设备条目，每条有 device_id 和 device_secret）

- [ ] **Step 4: 启动模拟器**

在新终端窗口：

```bash
python scripts/device_simulator.py
```

期望日志（示例）：
```
[10:01:00] INFO [卧室-light]: Connected, subscribed to $oc/devices/3a2.../sys/commands/#
[10:01:00] INFO [卧室-light]: Properties reported: {'on': False, 'color': '白色', 'brightness': 0}
...（7 行，每台设备一行）
```

- [ ] **Step 5: 运行单元测试套件（不需要 IoTDA 网络）**

```bash
pytest tests/test_device_registry.py tests/test_iotda_client.py -v
```

期望：全部 PASS（11 个测试）

- [ ] **Step 6: 启动 FastAPI 服务**

在另一个终端：

```bash
uvicorn app.main:app --reload
```

- [ ] **Step 7: 发送设备控制指令**

```bash
curl -s -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "smoke-test-1", "message": "把卧室灯打开"}' | python -m json.tool
```

**验收标准：**
1. 模拟器终端打印：`[卧室-light]: Command received: SetLight {'on': True, 'brightness': 80, 'color': '白色'}`
2. API 返回 `"intent": "device_control"` 且 `"response"` 包含"打开"
3. IoTDA 控制台 → 设备 → 卧室-light → 设备影子 → reported.on = true

- [ ] **Step 8: 发送场景指令**

```bash
curl -s -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "smoke-test-2", "message": "启动睡眠模式"}' | python -m json.tool
```

**验收标准：**
1. 模拟器打印 3 条命令日志（关卧室灯、设卧室空调、关卧室窗帘）
2. API 返回 `"intent": "scene"` 且 response 包含"睡眠模式"

- [ ] **Step 9: 最终提交**

```bash
git add config/iotda_devices.yml
git commit -m "feat(iotda): smoke test passed, commit generated device registry"
```

> **注意：** `config/iotda_devices.yml` 含有 `device_secret`，不要推送到公开仓库。确认 `.gitignore` 已包含 `config/iotda_devices.yml`。

---

## 已知注意事项

### SDK 类名不确定性

Task 3 / Task 8 中使用的 SDK model 类名（`SyncDeviceCommand`、`CreateProductRequestBody` 等）基于 SDK 命名规律推断。若导入失败，运行以下命令查看实际类名：

```bash
python -c "import huaweicloudsdkiotda.v5.model as m; [print(x) for x in sorted(dir(m)) if not x.startswith('_')]"
```

### MQTT 密码公式

Task 7 中使用 `HMAC-SHA256(device_secret, client_id)`。若连接失败（rc=5 认证拒绝），参考 [华为云 IoTDA MQTT 接入文档](https://support.huaweicloud.com/devg-iothub/iot_01_2127.html) 确认当前版本的密码计算公式。

### iotda_devices.yml 安全

该文件含 device_secret，需加入 `.gitignore`（见 Task 9 Step 9）。
