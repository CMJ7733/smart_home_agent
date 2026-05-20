import time

from huaweicloudsdkcore.auth.credentials import BasicCredentials
from huaweicloudsdkcore.exceptions.exceptions import ClientRequestException
from huaweicloudsdkiotda.v5 import IoTDAClient as _HWClient
from huaweicloudsdkiotda.v5.model import (
    CreateCommandRequest,      # outer request wrapper: device_id + body
    DeviceCommandRequest,      # inner body: service_id, command_name, paras
    ShowDeviceShadowRequest,   # shadow query: device_id
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

    def _build_command_request(
        self, device_id: str, service_id: str, command_name: str, params: dict
    ) -> CreateCommandRequest:
        body = DeviceCommandRequest(
            service_id=service_id,
            command_name=command_name,
            paras=params,
        )
        return CreateCommandRequest(device_id=device_id, body=body)

    def send_sync_command(
        self, device_id: str, service_id: str, command_name: str, params: dict
    ) -> dict:
        """Send a synchronous command to a device, retrying once on HTTP 429."""
        request = self._build_command_request(device_id, service_id, command_name, params)
        for attempt in range(2):
            try:
                response = self._client.create_command(request)
                return response.to_dict()
            except ClientRequestException as exc:
                if exc.status_code == 429 and attempt == 0:
                    time.sleep(1)
                    continue
                raise IotdaError(exc.error_code, exc.error_msg) from exc

    def get_device_shadow(self, device_id: str) -> dict:
        """Read the device shadow (reported + desired state) for a device."""
        request = ShowDeviceShadowRequest(device_id=device_id)
        try:
            response = self._client.show_device_shadow(request)
            return response.to_dict()
        except ClientRequestException as exc:
            raise IotdaError(exc.error_code, exc.error_msg) from exc
