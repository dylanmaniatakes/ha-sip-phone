"""Tests for SIP Phone's MQTT transport model."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock

from custom_components.sip_phone.client import SipPhoneClient
from custom_components.sip_phone.const import (
    CONF_COMMAND_TOPIC,
    CONF_DEFAULT_ACCOUNT,
    CONF_EVENT_TOPIC,
    CONF_SIP_DOMAIN,
    EVENT_CALL,
)


def _client() -> tuple[SipPhoneClient, MagicMock]:
    hass = MagicMock()
    client = SipPhoneClient(
        hass,
        "entry-1",
        {
            CONF_COMMAND_TOPIC: "sip/commands",
            CONF_DEFAULT_ACCOUNT: 1,
            CONF_EVENT_TOPIC: "sip/events",
            CONF_SIP_DOMAIN: "pbx.local",
        },
    )
    return client, hass


class SipPhoneClientTest(unittest.TestCase):
    """Verify URI formatting and event-driven state changes."""

    def test_format_destination(self) -> None:
        """Plain extensions and explicit SIP addresses are handled correctly."""
        client, _ = _client()
        self.assertEqual(client.format_destination("201"), "sip:201@pbx.local")
        self.assertEqual(client.format_destination("201@other.local"), "sip:201@other.local")
        self.assertEqual(client.format_destination("sips:201@secure.local"), "sips:201@secure.local")

    def test_event_updates_state_and_reemits_home_assistant_event(self) -> None:
        """Matching gateway events update the status sensor model."""
        client, hass = _client()
        listener = MagicMock()
        client.async_add_listener(listener)

        asyncio.run(client._async_handle_event(SimpleNamespace(payload='{"event":"call_established","sip_account":1,"internal_id":"call-1"}')))

        self.assertEqual(client.call_state, "connected")
        self.assertEqual(client.last_event["internal_id"], "call-1")
        hass.bus.async_fire.assert_called_once_with(
            EVENT_CALL,
            {"entry_id": "entry-1", "event": "call_established", "sip_account": 1, "internal_id": "call-1"},
        )
        listener.assert_called_once()

    def test_event_for_another_account_is_ignored(self) -> None:
        """A configured extension must not show another account's calls."""
        client, hass = _client()

        asyncio.run(client._async_handle_event(SimpleNamespace(payload='{"event":"call_established","sip_account":2}')))

        self.assertEqual(client.call_state, "idle")
        hass.bus.async_fire.assert_not_called()
