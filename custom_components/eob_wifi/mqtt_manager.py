from __future__ import annotations

import asyncio
import logging
import random
import string
import threading
from typing import Any, Callable

import paho.mqtt.client as mqtt

from .const import (
    DOMAIN,
    LOGGER,
    MQTT_BROKER_HOST,
    MQTT_BROKER_PORT,
    MQTT_BROKER_WS_PATH,
    MQTT_KEEPALIVE,
    MQTT_CLIENT_ID_PREFIX,
    TOPIC_BASE,
)

_CLIENT_ID_CHARS = string.ascii_letters + string.digits


def _generate_client_id() -> str:
    suffix = "".join(random.choice(_CLIENT_ID_CHARS) for _ in range(18))
    return MQTT_CLIENT_ID_PREFIX + suffix


def _get_topic_base(device_type: int) -> str | None:
    return TOPIC_BASE.get(device_type)


def _make_username(device_type: int, unique_id: int) -> str:
    base = _get_topic_base(device_type)
    return f"{base}_{str(unique_id).zfill(6)}"


def _make_sub_topic(device_type: int, unique_id: int) -> str:
    base = _get_topic_base(device_type)
    return f"{base}/O/{str(unique_id).zfill(6)}"


def _make_pub_topic(device_type: int, unique_id: int) -> str:
    base = _get_topic_base(device_type)
    return f"{base}/I/{str(unique_id).zfill(6)}"


def _build_binary_message(
    type_byte1: int, type_byte2: int, payload: bytes, msg_id: int | None = None
) -> bytes:
    if msg_id is None:
        msg_id = random.randint(0, 63999)
    header = bytes([type_byte1, type_byte2])
    header += msg_id.to_bytes(2, "big")
    header += len(payload).to_bytes(2, "big")
    return header + payload


def _build_therm_data_payload(temperature: float, is_analog_mode: bool = False) -> bytes:
    temp_int = max(0, min(78, int(round(temperature * 2))))
    mode_byte = 0
    if is_analog_mode:
        mode_byte |= 0x01
    return bytes([temp_int, mode_byte])


def _build_output_on_payload(turn_on: bool) -> bytes:
    return bytes([1 if turn_on else 0])


def _build_status_payload(
    output_index: int,
    mode: str,
    desired_temp: float | None = None,
    should_ignore_desired: bool = False,
    is_time_managed_by_ntp: bool = False,
    is_keyboard_locked: bool = False,
) -> bytes:
    mode_byte = 0
    if mode == "auto":
        mode_byte |= 0x01
    if should_ignore_desired:
        mode_byte |= 0x04
    if is_time_managed_by_ntp:
        mode_byte |= 0x20
    if is_keyboard_locked:
        mode_byte |= 0x40

    data = bytearray(3)
    data[0] = output_index
    data[1] = mode_byte
    if desired_temp is not None and not should_ignore_desired:
        data[2] = max(0, min(78, int(round(desired_temp * 2))))
    return bytes(data)


class DeviceMqttClient:
    def __init__(self, hass: Any, device: dict) -> None:
        self.hass = hass
        self._device = device
        self._device_id = device.get("deviceId")
        self._device_type = device.get("deviceType")
        self._unique_id = device.get("uniqueIdentifier")
        self._mqtt_pass = device.get("mqttPass")

        if not self._unique_id or not self._mqtt_pass:
            raise ValueError(f"Device {self._device_id} missing MQTT credentials")

        self._username = _make_username(self._device_type, self._unique_id)
        self._sub_topic = _make_sub_topic(self._device_type, self._unique_id)
        self._pub_topic = _make_pub_topic(self._device_type, self._unique_id)

        self._client = mqtt.Client(
            client_id=_generate_client_id(),
            transport="websockets",
        )
        self._client.ws_set_options(path=MQTT_BROKER_WS_PATH)
        self._client.username_pw_set(self._username, self._mqtt_pass)
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._client.on_disconnect = self._on_disconnect

        self._connected = threading.Event()
        self._response_futures: dict[int, asyncio.Future] = {}
        self._msg_id_counter = random.randint(0, 32000)
        self._raw_message_callback: Callable[[bytes], None] | None = None

    @property
    def is_connected(self) -> bool:
        return self._connected.is_set()

    @property
    def device_id(self):
        return self._device_id

    def _next_msg_id(self) -> int:
        self._msg_id_counter = (self._msg_id_counter + 1) % 64000
        return self._msg_id_counter

    def _on_connect(self, client, userdata, flags, rc) -> None:
        if rc == 0:
            client.subscribe(self._sub_topic)
            self._connected.set()
            LOGGER.info("MQTT connected for device %s", self._device_id)
        else:
            LOGGER.error(
                "MQTT connection failed for device %s: rc=%d", self._device_id, rc
            )

    def _on_disconnect(self, client, userdata, rc) -> None:
        self._connected.clear()
        LOGGER.debug("MQTT disconnected for device %s", self._device_id)

    def _on_message(self, client, userdata, msg) -> None:
        data = bytes(msg.payload)
        if len(data) < 6:
            return
        msg_id = (data[2] << 8) | data[3]
        future = self._response_futures.pop(msg_id, None)
        if future is not None and not future.done():
            self.hass.loop.call_soon_threadsafe(future.set_result, data)
        if self._raw_message_callback is not None:
            self.hass.loop.call_soon_threadsafe(self._raw_message_callback, data)

    async def connect(self) -> None:
        await self.hass.async_add_executor_job(
            self._client.tls_set
        )
        self._client.connect_async(MQTT_BROKER_HOST, MQTT_BROKER_PORT, MQTT_KEEPALIVE)
        self._client.loop_start()
        LOGGER.info("MQTT client starting for device %s", self._device_id)

    async def disconnect(self) -> None:
        self._client.loop_stop()
        self._client.disconnect()
        self._connected.clear()
        LOGGER.info("MQTT client disconnected for device %s", self._device_id)

    async def publish_and_wait(
        self,
        type_byte1: int,
        type_byte2: int,
        payload: bytes,
        timeout: float = 5.0,
    ) -> bytes | None:
        if not self._connected.is_set():
            LOGGER.warning("MQTT not connected for device %s", self._device_id)
            return None

        msg_id = self._next_msg_id()
        full_msg = _build_binary_message(type_byte1, type_byte2, payload, msg_id)

        future: asyncio.Future = asyncio.Future()
        self._response_futures[msg_id] = future

        self._client.publish(self._pub_topic, full_msg)

        try:
            return await asyncio.wait_for(future, timeout)
        except asyncio.TimeoutError:
            self._response_futures.pop(msg_id, None)
            LOGGER.debug(
                "MQTT response timeout for device %s msg_id=%d",
                self._device_id,
                msg_id,
            )
            return None

    def publish_fire_and_forget(
        self,
        type_byte1: int,
        type_byte2: int,
        payload: bytes,
    ) -> None:
        if not self._connected.is_set():
            LOGGER.warning("MQTT not connected for device %s", self._device_id)
            return
        msg_id = self._next_msg_id()
        full_msg = _build_binary_message(type_byte1, type_byte2, payload, msg_id)
        self._client.publish(self._pub_topic, full_msg)

    def set_raw_message_callback(self, callback: Callable[[bytes], None]) -> None:
        self._raw_message_callback = callback


class MqttManager:
    def __init__(self, hass: Any) -> None:
        self.hass = hass
        self._clients: dict[int, DeviceMqttClient] = {}

    async def add_device(self, device: dict) -> DeviceMqttClient | None:
        device_id = device.get("deviceId")
        if device_id in self._clients:
            return self._clients[device_id]
        try:
            client = DeviceMqttClient(self.hass, device)
            await client.connect()
            self._clients[device_id] = client
            return client
        except ValueError as e:
            LOGGER.warning("Skipping MQTT for device %s: %s", device_id, e)
            return None

    def get_client(self, device_id: int) -> DeviceMqttClient | None:
        return self._clients.get(device_id)

    async def remove_device(self, device_id: int) -> None:
        client = self._clients.pop(device_id, None)
        if client is not None:
            await client.disconnect()

    async def shutdown(self) -> None:
        for device_id in list(self._clients):
            await self.remove_device(device_id)

    async def set_thermostat_temp(self, device_id: int, temperature: float, is_analog_mode: bool = False) -> bool:
        client = self.get_client(device_id)
        if client is None:
            return False
        payload = _build_therm_data_payload(temperature, is_analog_mode)
        client.publish_fire_and_forget(0x10, 0x0B, payload)
        return True

    async def set_relay_state(self, device_id: int, turn_on: bool) -> bool:
        client = self.get_client(device_id)
        if client is None:
            return False
        payload = _build_output_on_payload(turn_on)
        client.publish_fire_and_forget(0x00, 0x01, payload)
        return True

    async def set_device_mode(
        self, device_id: int, mode: str, desired_temp: float | None = None
    ) -> bool:
        client = self.get_client(device_id)
        if client is None:
            return False
        should_ignore = mode == "off"
        payload = _build_status_payload(
            output_index=1,
            mode=mode,
            desired_temp=desired_temp if not should_ignore else None,
            should_ignore_desired=should_ignore,
        )
        client.publish_fire_and_forget(0x00, 0x02, payload)
        return True
