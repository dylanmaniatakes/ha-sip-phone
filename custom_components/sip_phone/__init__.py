"""Home Assistant integration for MQTT-connected SIP extensions."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv

from .client import SipPhoneClient
from .const import (
    ATTR_DESTINATION, ATTR_DIGITS, ATTR_ENTRY_ID, ATTR_METHOD, ATTR_RING_TIMEOUT,
    ATTR_SIP_ACCOUNT, ATTR_SIP_CODE, DATA_CLIENTS, DOMAIN, DTMF_METHODS, PLATFORMS,
    SERVICE_ANSWER, SERVICE_DIAL, SERVICE_HANGUP, SERVICE_SEND_DTMF,
)

SERVICE_BASE_SCHEMA = vol.Schema({
    vol.Optional(ATTR_ENTRY_ID): cv.string,
    vol.Optional(ATTR_SIP_ACCOUNT): vol.All(vol.Coerce(int), vol.Range(min=1, max=3)),
})


def _schema(extra: dict[Any, Any] | None = None) -> vol.Schema:
    """Extend the shared action schema."""
    return SERVICE_BASE_SCHEMA.extend(extra or {})


async def async_setup(hass: HomeAssistant, _: dict[str, Any]) -> bool:
    """Register actions once for all configured SIP extensions."""
    hass.data.setdefault(DOMAIN, {DATA_CLIENTS: {}})
    hass.services.async_register(DOMAIN, SERVICE_DIAL, _async_dial, schema=_schema({
        vol.Required(ATTR_DESTINATION): cv.string,
        vol.Optional(ATTR_RING_TIMEOUT): vol.All(vol.Coerce(float), vol.Range(min=1, max=3600)),
    }))
    hass.services.async_register(DOMAIN, SERVICE_HANGUP, _async_hangup, schema=_schema({
        vol.Required(ATTR_DESTINATION): cv.string,
        vol.Optional(ATTR_SIP_CODE): vol.All(vol.Coerce(int), vol.Range(min=0, max=699)),
    }))
    hass.services.async_register(DOMAIN, SERVICE_ANSWER, _async_answer, schema=_schema({
        vol.Required(ATTR_DESTINATION): cv.string,
    }))
    hass.services.async_register(DOMAIN, SERVICE_SEND_DTMF, _async_send_dtmf, schema=_schema({
        vol.Required(ATTR_DESTINATION): cv.string,
        vol.Required(ATTR_DIGITS): vol.All(cv.string, vol.Length(min=1, max=64)),
        vol.Optional(ATTR_METHOD, default="rfc2833"): vol.In(DTMF_METHODS),
    }))
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up one configured SIP extension."""
    client = SipPhoneClient(hass, entry.entry_id, {**entry.data, **entry.options})
    await client.async_start()
    hass.data[DOMAIN][DATA_CLIENTS][entry.entry_id] = client
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload one configured SIP extension."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        client: SipPhoneClient = hass.data[DOMAIN][DATA_CLIENTS].pop(entry.entry_id)
        await client.async_stop()
    return unloaded


def _get_client(hass: HomeAssistant, call: ServiceCall) -> SipPhoneClient:
    """Resolve the requested extension, avoiding silent routing ambiguity."""
    clients: dict[str, SipPhoneClient] = hass.data[DOMAIN][DATA_CLIENTS]
    entry_id = call.data.get(ATTR_ENTRY_ID)
    if entry_id:
        if client := clients.get(entry_id):
            return client
        raise HomeAssistantError("The requested SIP Phone entry is not loaded")
    if len(clients) == 1:
        return next(iter(clients.values()))
    if not clients:
        raise HomeAssistantError("No SIP Phone entries are loaded")
    raise HomeAssistantError("Specify entry_id when more than one SIP Phone entry is configured")


def _command_target(client: SipPhoneClient, call: ServiceCall) -> tuple[str, int]:
    """Return the gateway call key and selected SIP account."""
    destination = call.data[ATTR_DESTINATION].strip()
    if destination == client.last_event.get("internal_id"):
        return destination, call.data.get(ATTR_SIP_ACCOUNT, client.default_account)
    return client.format_destination(destination), call.data.get(ATTR_SIP_ACCOUNT, client.default_account)


async def _async_dial(call: ServiceCall) -> None:
    """Start an outgoing SIP call."""
    client = _get_client(call.hass, call)
    destination, account = _command_target(client, call)
    command: dict[str, Any] = {"command": "dial", "number": destination, "sip_account": account}
    if ATTR_RING_TIMEOUT in call.data:
        command[ATTR_RING_TIMEOUT] = call.data[ATTR_RING_TIMEOUT]
    await client.async_send(command)


async def _async_hangup(call: ServiceCall) -> None:
    """End an active or ringing SIP call."""
    client = _get_client(call.hass, call)
    destination, account = _command_target(client, call)
    command: dict[str, Any] = {"command": "hangup", "number": destination, "sip_account": account}
    if ATTR_SIP_CODE in call.data:
        command[ATTR_SIP_CODE] = call.data[ATTR_SIP_CODE]
    await client.async_send(command)


async def _async_answer(call: ServiceCall) -> None:
    """Answer a ringing SIP call by its internal call ID."""
    client = _get_client(call.hass, call)
    destination = call.data[ATTR_DESTINATION].strip()
    account = call.data.get(ATTR_SIP_ACCOUNT, client.default_account)
    await client.async_send({"command": "answer", "number": destination, "sip_account": account})


async def _async_send_dtmf(call: ServiceCall) -> None:
    """Send DTMF digits to an active SIP call."""
    client = _get_client(call.hass, call)
    destination, account = _command_target(client, call)
    await client.async_send({"command": "send_dtmf", "number": destination, "sip_account": account, "digits": call.data[ATTR_DIGITS], "method": call.data[ATTR_METHOD]})
