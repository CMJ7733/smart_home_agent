import re
import time

import requests


class IotdaError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"IoTDA [{code}]: {message}")


class IotdaClient:
    """IoTDA REST client using IAM Token auth (required for dedicated instances)."""

    _TOKEN_TTL = 86400  # IAM token lives 24h; refresh 5min before expiry

    def __init__(self, endpoint: str, project_id: str, ak: str, sk: str):
        self._endpoint = endpoint
        self._project_id = project_id
        self._ak = ak
        self._sk = sk
        self._token: str | None = None
        self._token_expires_at: float = 0
        # Derive region from endpoint: "....cn-north-4.myhuaweicloud.com" → "cn-north-4"
        m = re.search(r"(cn-[a-z]+-\d+)\.myhuaweicloud\.com", endpoint)
        self._region = m.group(1) if m else "cn-north-4"

    def _get_token(self) -> str:
        if self._token and time.time() < self._token_expires_at - 300:
            return self._token
        resp = requests.post(
            f"https://iam.{self._region}.myhuaweicloud.com/v3/auth/tokens",
            json={
                "auth": {
                    "identity": {
                        "methods": ["hw_ak_sk"],
                        "hw_ak_sk": {
                            "access": {"key": self._ak},
                            "secret": {"key": self._sk},
                        },
                    },
                    "scope": {"project": {"id": self._project_id}},
                }
            },
            timeout=10,
        )
        if resp.status_code != 201:
            raise IotdaError(
                "IAM_AUTH_FAILED",
                f"IAM token request failed ({resp.status_code}): {resp.text[:200]}",
            )
        self._token = resp.headers["X-Subject-Token"]
        self._token_expires_at = time.time() + self._TOKEN_TTL
        return self._token

    def _headers(self) -> dict:
        return {"X-Auth-Token": self._get_token(), "Content-Type": "application/json"}

    def send_sync_command(
        self, device_id: str, service_id: str, command_name: str, params: dict
    ) -> dict:
        url = f"https://{self._endpoint}/v5/iot/{self._project_id}/devices/{device_id}/commands"
        body = {"service_id": service_id, "command_name": command_name, "paras": params}
        for attempt in range(2):
            try:
                resp = requests.post(url, headers=self._headers(), json=body, timeout=25)
            except requests.exceptions.Timeout:
                raise IotdaError("TIMEOUT", f"Command timed out for device {device_id}")

            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", 1))
                if attempt == 0:
                    time.sleep(retry_after)
                    continue
                raise IotdaError("RATE_LIMITED", f"Still rate-limited after retry ({device_id})")

            if not resp.ok:
                error = resp.json() if resp.content else {}
                error_code = error.get("error_code", f"HTTP_{resp.status_code}")
                error_msg = error.get("error_msg", resp.text[:200])
                if error_code == "IOTDA.014011":
                    raise IotdaError(error_code, f"设备离线 ({device_id})，请确认模拟器已启动")
                raise IotdaError(error_code, error_msg)

            return resp.json()

    def get_device_info(self, device_id: str) -> dict:
        """Returns device info including `status` field: ONLINE | OFFLINE | ABNORMAL | INACTIVE."""
        url = f"https://{self._endpoint}/v5/iot/{self._project_id}/devices/{device_id}"
        try:
            resp = requests.get(url, headers=self._headers(), timeout=10)
        except requests.exceptions.Timeout:
            raise IotdaError("TIMEOUT", f"Device info query timed out for device {device_id}")
        if not resp.ok:
            error = resp.json() if resp.content else {}
            raise IotdaError(
                error.get("error_code", f"HTTP_{resp.status_code}"),
                error.get("error_msg", resp.text[:200]),
            )
        return resp.json()

    def get_device_shadow(self, device_id: str) -> dict:
        url = f"https://{self._endpoint}/v5/iot/{self._project_id}/devices/{device_id}/shadow"
        try:
            resp = requests.get(url, headers=self._headers(), timeout=10)
        except requests.exceptions.Timeout:
            raise IotdaError("TIMEOUT", f"Shadow query timed out for device {device_id}")
        if not resp.ok:
            error = resp.json() if resp.content else {}
            raise IotdaError(
                error.get("error_code", f"HTTP_{resp.status_code}"),
                error.get("error_msg", resp.text[:200]),
            )
        return resp.json()
