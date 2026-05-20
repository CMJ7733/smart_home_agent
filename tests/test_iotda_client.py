import pytest
from unittest.mock import MagicMock, patch
from app.tools.iotda_client import IotdaClient, IotdaError


def _make_client():
    return IotdaClient("ep.st1.iotda-app.cn-north-4.myhuaweicloud.com", "proj", "ak", "sk")


def _mock_token(mock_post):
    """Configure mock_post to return a valid IAM token on the first call."""
    token_resp = MagicMock()
    token_resp.status_code = 201
    token_resp.headers = {"X-Subject-Token": "test-token"}
    mock_post.return_value = token_resp
    return token_resp


@pytest.fixture(autouse=True)
def freeze_token(monkeypatch):
    """Pre-seed a valid token so tests don't hit IAM unless explicitly testing auth."""
    client_store = {}

    original_init = IotdaClient.__init__

    def patched_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self._token = "pre-seeded-token"
        self._token_expires_at = float("inf")

    monkeypatch.setattr(IotdaClient, "__init__", patched_init)


def test_send_sync_command_success():
    client = _make_client()
    ok_resp = MagicMock()
    ok_resp.status_code = 201
    ok_resp.ok = True
    ok_resp.json.return_value = {"command_id": "cmd-1", "status": "DELIVERED"}

    with patch("app.tools.iotda_client.requests.post", return_value=ok_resp) as mock_post:
        result = client.send_sync_command("dev-1", "LightControl", "SetLight", {"on": True})

    assert result == {"command_id": "cmd-1", "status": "DELIVERED"}
    mock_post.assert_called_once()
    call_kwargs = mock_post.call_args
    assert "dev-1" in call_kwargs.args[0]
    assert call_kwargs.kwargs["json"]["command_name"] == "SetLight"


def test_send_sync_command_4xx_raises_iotda_error():
    client = _make_client()
    err_resp = MagicMock()
    err_resp.status_code = 404
    err_resp.ok = False
    err_resp.content = b'{"error_code":"IOTDA.000404","error_msg":"device not found"}'
    err_resp.json.return_value = {"error_code": "IOTDA.000404", "error_msg": "device not found"}

    with patch("app.tools.iotda_client.requests.post", return_value=err_resp):
        with pytest.raises(IotdaError, match="IOTDA.000404"):
            client.send_sync_command("dev-x", "SvcA", "CmdA", {})


def test_send_sync_command_429_retries_once():
    client = _make_client()
    resp_429 = MagicMock()
    resp_429.status_code = 429
    resp_429.ok = False
    resp_429.headers = {"Retry-After": "1"}

    resp_ok = MagicMock()
    resp_ok.status_code = 201
    resp_ok.ok = True
    resp_ok.json.return_value = {"status": "DELIVERED"}

    with patch("app.tools.iotda_client.requests.post", side_effect=[resp_429, resp_ok]) as mock_post:
        with patch("app.tools.iotda_client.time.sleep") as mock_sleep:
            result = client.send_sync_command("dev-1", "SvcA", "CmdA", {})

    assert result == {"status": "DELIVERED"}
    mock_sleep.assert_called_once_with(1)
    assert mock_post.call_count == 2


def test_send_sync_command_429_twice_raises():
    client = _make_client()
    resp_429 = MagicMock()
    resp_429.status_code = 429
    resp_429.ok = False
    resp_429.headers = {"Retry-After": "1"}

    with patch("app.tools.iotda_client.requests.post", side_effect=[resp_429, resp_429]):
        with patch("app.tools.iotda_client.time.sleep"):
            with pytest.raises(IotdaError, match="RATE_LIMITED"):
                client.send_sync_command("dev-1", "SvcA", "CmdA", {})


def test_get_device_shadow_success():
    client = _make_client()
    ok_resp = MagicMock()
    ok_resp.ok = True
    ok_resp.json.return_value = {
        "device_id": "dev-1",
        "shadow": [{"service_id": "LightControl",
                    "reported": {"properties": {"on": True, "brightness": 80}}}],
    }

    with patch("app.tools.iotda_client.requests.get", return_value=ok_resp):
        result = client.get_device_shadow("dev-1")

    assert result["shadow"][0]["reported"]["properties"]["on"] is True


def test_get_device_shadow_error():
    client = _make_client()
    err_resp = MagicMock()
    err_resp.ok = False
    err_resp.content = b'{"error_code":"IOTDA.000404","error_msg":"not found"}'
    err_resp.json.return_value = {"error_code": "IOTDA.000404", "error_msg": "not found"}

    with patch("app.tools.iotda_client.requests.get", return_value=err_resp):
        with pytest.raises(IotdaError, match="IOTDA.000404"):
            client.get_device_shadow("dev-x")


def test_iam_token_refresh():
    """Token is fetched from IAM when cache is expired."""
    client = _make_client()
    client._token = None
    client._token_expires_at = 0

    token_resp = MagicMock()
    token_resp.status_code = 201
    token_resp.headers = {"X-Subject-Token": "fresh-token"}

    ok_resp = MagicMock()
    ok_resp.ok = True
    ok_resp.json.return_value = {"device_id": "dev-1", "shadow": []}

    with patch("app.tools.iotda_client.requests.post", return_value=token_resp) as mock_post:
        with patch("app.tools.iotda_client.requests.get", return_value=ok_resp):
            client.get_device_shadow("dev-1")

    mock_post.assert_called_once()
    assert "iam.cn-north-4.myhuaweicloud.com" in mock_post.call_args.args[0]
    assert client._token == "fresh-token"
