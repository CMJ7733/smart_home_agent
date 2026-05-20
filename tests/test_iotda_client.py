import pytest
from unittest.mock import MagicMock, patch, call
from huaweicloudsdkcore.exceptions.exceptions import ClientRequestException, SdkError
from app.tools.iotda_client import IotdaClient, IotdaError


def _make_exc(status_code: int, error_code: str, error_msg: str) -> ClientRequestException:
    """Helper: build a ClientRequestException with the installed SDK's constructor."""
    sdk_err = SdkError(request_id="r1", error_code=error_code, error_msg=error_msg)
    return ClientRequestException(status_code, sdk_err)


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
    hw_instance.create_command.return_value = mock_resp

    client = IotdaClient("ep.com", "proj", "ak", "sk")
    result = client.send_sync_command("dev-1", "LightControl", "SetLight", {"on": True})

    assert result == {"command_id": "cmd-1", "status": "DELIVERED"}
    hw_instance.create_command.assert_called_once()


def test_send_sync_command_4xx_raises_iotda_error(hw_instance):
    exc = _make_exc(404, "IOTDA.000404", "device not found")
    hw_instance.create_command.side_effect = exc

    client = IotdaClient("ep.com", "proj", "ak", "sk")
    with pytest.raises(IotdaError, match="IOTDA.000404"):
        client.send_sync_command("dev-x", "SvcA", "CmdA", {})


def test_send_sync_command_429_retries_once(hw_instance):
    exc_429 = _make_exc(429, "APIG.0308", "throttled")
    ok_resp = MagicMock()
    ok_resp.to_dict.return_value = {"status": "DELIVERED"}
    hw_instance.create_command.side_effect = [exc_429, ok_resp]

    client = IotdaClient("ep.com", "proj", "ak", "sk")
    with patch("app.tools.iotda_client.time.sleep") as mock_sleep:
        result = client.send_sync_command("dev-1", "SvcA", "CmdA", {})

    assert result == {"status": "DELIVERED"}
    mock_sleep.assert_called_once_with(1)
    assert hw_instance.create_command.call_count == 2


def test_send_sync_command_429_twice_raises(hw_instance):
    exc_429 = _make_exc(429, "APIG.0308", "throttled")
    hw_instance.create_command.side_effect = [exc_429, exc_429]

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
    exc = _make_exc(404, "IOTDA.000404", "not found")
    hw_instance.show_device_shadow.side_effect = exc

    client = IotdaClient("ep.com", "proj", "ak", "sk")
    with pytest.raises(IotdaError, match="IOTDA.000404"):
        client.get_device_shadow("dev-x")
