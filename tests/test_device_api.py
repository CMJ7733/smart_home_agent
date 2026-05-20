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
