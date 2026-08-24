"""MQTT transport and state model for SIP Phone."""

from __future__ import annotations

from collections.abc import Callable
import asyncio
import json
import logging
from typing import Any

from homeassistant.components import mqtt
from homeassistant.core import HomeAssistant

from .const import CONF_ASSISTANT_URI, CONF_COMMAND_TOPIC, CONF_DEFAULT_ACCOUNT, CONF_EVENT_TOPIC, CONF_SIP_DOMAIN, EVENT_CALL

_LOGGER = logging.getLogger(__name__)
StateListener = Callable[[], None]


class SipPhoneClient:
    """Bridge one SIP extension to an MQTT-enabled SIP gateway."""

    def __init__(self, hass: HomeAssistant, entry_id: str, data: dict[str, Any]) -> None:
        self.hass = hass
        self.entry_id = entry_id
        self.command_topic: str = data[CONF_COMMAND_TOPIC]
        self.assistant_uri: str = data.get(CONF_ASSISTANT_URI, "").strip()
        self.event_topic: str = data[CONF_EVENT_TOPIC]
        self.sip_domain: str = data[CONF_SIP_DOMAIN]
        self.default_account: int = data[CONF_DEFAULT_ACCOUNT]
        self.call_state = "idle"
        self.last_event: dict[str, Any] = {}
        self._listeners: list[StateListener] = []
        self._unsubscribe: Callable[[], None] | None = None

    async def async_start(self) -> None:
        """Wait for MQTT and receive status notifications from the gateway."""
        await mqtt.async_wait_for_mqtt_client(self.hass)
        self._unsubscribe = await mqtt.async_subscribe(self.hass, self.event_topic, self._async_handle_event, qos=1)

    async def async_stop(self) -> None:
        """Stop receiving gateway events."""
        if self._unsubscribe is not None:
            self._unsubscribe()
            self._unsubscribe = None

    def async_add_listener(self, listener: StateListener) -> Callable[[], None]:
        """Register a callback for state changes."""
        self._listeners.append(listener)

        def remove_listener() -> None:
            if listener in self._listeners:
                self._listeners.remove(listener)

        return remove_listener

    def format_destination(self, destination: str) -> str:
        """Turn a plain extension into an address on the configured SIP domain."""
        destination = destination.strip()
        if destination.lower().startswith(("sip:", "sips:")):
            return destination
        if "@" in destination:
            return f"sip:{destination}"
        return f"sip:{destination}@{self.sip_domain}"

    async def async_send(self, command: dict[str, Any]) -> None:
        """Publish a command understood by ha-sip's MQTT command client."""
        await mqtt.async_publish(self.hass, self.command_topic, json.dumps(command), qos=1, retain=False)

    async def async_wait_for_event(self, predicate: Callable[[dict[str, Any]], bool], timeout: float) -> dict[str, Any]:
        """Wait for a gateway event matching a specific call lifecycle condition."""
        if predicate(self.last_event):
            return self.last_event
        future: asyncio.Future[dict[str, Any]] = asyncio.get_running_loop().create_future()

        def event_received() -> None:
            if not future.done() and predicate(self.last_event):
                future.set_result(self.last_event)

        unsubscribe = self.async_add_listener(event_received)
        try:
            return await asyncio.wait_for(future, timeout)
        finally:
            unsubscribe()

    async def _async_handle_event(self, message: mqtt.ReceiveMessage) -> None:
        """Update the Home Assistant representation of a gateway call event."""
        try:
            event = json.loads(message.payload)
        except (TypeError, json.JSONDecodeError):
            _LOGGER.warning("Ignoring invalid JSON on SIP event topic %s", self.event_topic)
            return
        if not isinstance(event, dict):
            _LOGGER.warning("Ignoring non-object SIP event on %s", self.event_topic)
            return
        account = event.get("sip_account")
        if account is not None and account != self.default_account:
            return
        event_name = event.get("event")
        if event_name in {"incoming_call", "outgoing_call_initiated"}:
            self.call_state = "ringing"
        elif event_name == "call_established":
            self.call_state = "connected"
        elif event_name in {"call_disconnected", "ring_timeout"}:
            self.call_state = "idle"
        self.last_event = event
        self.hass.bus.async_fire(EVENT_CALL, {"entry_id": self.entry_id, **event})
        for listener in tuple(self._listeners):
            listener()
