"""Call status entity for SIP Phone."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .client import SipPhoneClient
from .const import CONF_DEFAULT_ACCOUNT, CONF_NAME, CONF_SIP_DOMAIN, DATA_CLIENTS, DOMAIN


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Add the call status sensor for one SIP extension."""
    async_add_entities([SipPhoneCallStatus(entry, hass.data[DOMAIN][DATA_CLIENTS][entry.entry_id])])


class SipPhoneCallStatus(SensorEntity):
    """Expose the most recent call state for an extension."""

    _attr_has_entity_name = True
    _attr_name = "Call status"
    _attr_icon = "mdi:phone-in-talk"
    _attr_should_poll = False

    def __init__(self, entry: ConfigEntry, client: SipPhoneClient) -> None:
        self._entry = entry
        self._client = client
        self._unsubscribe: Callable[[], None] | None = None
        self._attr_unique_id = f"{entry.entry_id}_call_status"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.data[CONF_NAME],
            manufacturer="SIP Phone",
            model="MQTT SIP extension",
        )

    @property
    def native_value(self) -> str:
        """Return the current call lifecycle state."""
        return self._client.call_state

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Make received call metadata available in the UI and automations."""
        return {"sip_domain": self._entry.data[CONF_SIP_DOMAIN], "sip_account": self._entry.data[CONF_DEFAULT_ACCOUNT], **self._client.last_event}

    async def async_added_to_hass(self) -> None:
        """Update immediately after a gateway event."""
        self._unsubscribe = self._client.async_add_listener(self.async_write_ha_state)

    async def async_will_remove_from_hass(self) -> None:
        """Release the state listener."""
        if self._unsubscribe is not None:
            self._unsubscribe()
            self._unsubscribe = None
