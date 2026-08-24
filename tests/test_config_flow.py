"""Tests for the SIP Phone configuration form."""

from __future__ import annotations

import unittest

from homeassistant.helpers.selector import TextSelector

from custom_components.sip_phone.config_flow import _schema, _valid_data
from custom_components.sip_phone.const import (
    CONF_COMMAND_TOPIC,
    CONF_DEFAULT_ACCOUNT,
    CONF_EVENT_TOPIC,
    CONF_NAME,
    CONF_SIP_DOMAIN,
)


class SipPhoneConfigFlowTest(unittest.TestCase):
    """Verify the friendly, typed configuration form."""

    def test_account_slot_uses_text_input(self) -> None:
        """The UI must not render the gateway account slot as a slider."""
        for key, value in _schema().schema.items():
            if key.schema == CONF_DEFAULT_ACCOUNT:
                self.assertIsInstance(value, TextSelector)
                return
        self.fail("The SIP account slot is missing from the config flow")

    def test_text_account_slot_is_validated(self) -> None:
        """Text input is accepted only for a gateway account slot from 1 to 3."""
        data = {
            CONF_NAME: "SIP Phone",
            CONF_SIP_DOMAIN: "pbx.local",
            CONF_DEFAULT_ACCOUNT: "1",
            CONF_COMMAND_TOPIC: "hasip/execute",
            CONF_EVENT_TOPIC: "hasip/state",
        }
        self.assertTrue(_valid_data(data))
        data[CONF_DEFAULT_ACCOUNT] = "4"
        self.assertFalse(_valid_data(data))
