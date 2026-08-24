"""Tests for SIP Phone automation actions."""

from __future__ import annotations

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock

from custom_components.sip_phone import _async_answer, _async_dial, _async_hangup
from custom_components.sip_phone.client import SipPhoneClient
from custom_components.sip_phone.const import (
    ATTR_DESTINATION,
    ATTR_RING_TIMEOUT,
    DATA_CLIENTS,
    DOMAIN,
    CONF_COMMAND_TOPIC,
    CONF_DEFAULT_ACCOUNT,
    CONF_EVENT_TOPIC,
    CONF_SIP_DOMAIN,
)


def _call(data: dict[str, object]) -> tuple[MagicMock, SipPhoneClient]:
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
    client.async_send = AsyncMock()
    hass.data = {DOMAIN: {DATA_CLIENTS: {"entry-1": client}}}
    call = MagicMock(hass=hass, data=data)
    return call, client


class SipPhoneServiceTest(unittest.TestCase):
    """Verify command payloads passed to the compatible gateway."""

    def test_dial_expands_a_plain_extension(self) -> None:
        """The user-facing destination field produces a SIP URI."""
        call, client = _call({ATTR_DESTINATION: "201", ATTR_RING_TIMEOUT: 20})

        asyncio.run(_async_dial(call))

        client.async_send.assert_awaited_once_with({"command": "dial", "number": "sip:201@pbx.local", "sip_account": 1, "ring_timeout": 20})

    def test_answer_preserves_incoming_internal_id(self) -> None:
        """Incoming calls are addressed by the gateway call ID, not a SIP URI."""
        call, client = _call({ATTR_DESTINATION: "call-1"})

        asyncio.run(_async_answer(call))

        client.async_send.assert_awaited_once_with({"command": "answer", "number": "call-1", "sip_account": 1})

    def test_hangup_preserves_current_incoming_call_id(self) -> None:
        """An incoming call can be ended from its call event identifier."""
        call, client = _call({ATTR_DESTINATION: "call-1"})
        client.last_event = {"internal_id": "call-1"}

        asyncio.run(_async_hangup(call))

        client.async_send.assert_awaited_once_with({"command": "hangup", "number": "call-1", "sip_account": 1})
