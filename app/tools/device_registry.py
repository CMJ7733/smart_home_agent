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
