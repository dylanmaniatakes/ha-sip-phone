"""Config flow for SIP Phone."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import TextSelector

from .const import (
    CONF_COMMAND_TOPIC, CONF_DEFAULT_ACCOUNT, CONF_EVENT_TOPIC, CONF_NAME, CONF_SIP_DOMAIN,
    DEFAULT_COMMAND_TOPIC, DEFAULT_EVENT_TOPIC, DEFAULT_NAME, DEFAULT_SIP_ACCOUNT, DOMAIN,
)


def _schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Return the user-facing connection schema."""
    defaults = defaults or {}
    return vol.Schema({
        vol.Required(CONF_NAME, default=defaults.get(CONF_NAME, DEFAULT_NAME)): str,
        vol.Required(CONF_SIP_DOMAIN, default=defaults.get(CONF_SIP_DOMAIN, "")): str,
        vol.Required(CONF_DEFAULT_ACCOUNT, default=str(defaults.get(CONF_DEFAULT_ACCOUNT, DEFAULT_SIP_ACCOUNT))): TextSelector(),
        vol.Required(CONF_COMMAND_TOPIC, default=defaults.get(CONF_COMMAND_TOPIC, DEFAULT_COMMAND_TOPIC)): str,
        vol.Required(CONF_EVENT_TOPIC, default=defaults.get(CONF_EVENT_TOPIC, DEFAULT_EVENT_TOPIC)): str,
    })


def _valid_data(data: dict[str, Any]) -> bool:
    """Reject values that cannot form a safe local SIP address or MQTT topic."""
    domain = data[CONF_SIP_DOMAIN].strip()
    command_topic = data[CONF_COMMAND_TOPIC].strip()
    event_topic = data[CONF_EVENT_TOPIC].strip()
    try:
        account = int(data[CONF_DEFAULT_ACCOUNT])
    except (TypeError, ValueError):
        return False
    return bool(domain and "/" not in domain and not domain.lower().startswith(("sip:", "sips:")) and command_topic and event_topic and 1 <= account <= 3 and not any(char in command_topic + event_topic for char in "#+"))


class SipPhoneConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a SIP Phone configuration entry."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Configure a SIP extension gateway."""
        errors: dict[str, str] = {}
        if user_input is not None:
            user_input = {key: value.strip() if isinstance(value, str) else value for key, value in user_input.items()}
            if not _valid_data(user_input):
                errors["base"] = "invalid_connection"
            else:
                user_input[CONF_DEFAULT_ACCOUNT] = int(user_input[CONF_DEFAULT_ACCOUNT])
                unique_id = f"{user_input[CONF_SIP_DOMAIN]}:{user_input[CONF_DEFAULT_ACCOUNT]}:{user_input[CONF_COMMAND_TOPIC]}"
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)
        return self.async_show_form(step_id="user", data_schema=_schema(user_input), errors=errors)

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> SipPhoneOptionsFlow:
        """Provide an options editor after initial setup."""
        return SipPhoneOptionsFlow()


class SipPhoneOptionsFlow(config_entries.OptionsFlow):
    """Edit SIP Phone connection settings."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the options form."""
        errors: dict[str, str] = {}
        if user_input is not None:
            user_input = {key: value.strip() if isinstance(value, str) else value for key, value in user_input.items()}
            if _valid_data(user_input):
                user_input[CONF_DEFAULT_ACCOUNT] = int(user_input[CONF_DEFAULT_ACCOUNT])
                return self.async_create_entry(title="", data=user_input)
            errors["base"] = "invalid_connection"
        defaults = {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(step_id="init", data_schema=_schema(defaults), errors=errors)
