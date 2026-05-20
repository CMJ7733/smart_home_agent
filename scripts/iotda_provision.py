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
    AddProduct,
    ServiceCapability,
    ServiceCommand,
    ServiceCommandPara,
    ServiceProperty,
    AddDeviceRequest,
    AddDevice,
)

load_dotenv()

ENDPOINT = os.environ["IOTDA_ENDPOINT"]
PROJECT_ID = os.environ["IOTDA_PROJECT_ID"]
AK = os.environ["IOTDA_AK"]
SK = os.environ["IOTDA_SK"]
OUTPUT_PATH = Path(__file__).parent.parent / "config" / "iotda_devices.yml"

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
        req.body = AddProduct(
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
        req = AddDeviceRequest()
        req.body = AddDevice(
            device_name=layout["name"],
            node_id=layout["name"],
            product_id=product_id,
        )
        resp = client.add_device(req)
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
