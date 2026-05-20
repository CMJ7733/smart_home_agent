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
