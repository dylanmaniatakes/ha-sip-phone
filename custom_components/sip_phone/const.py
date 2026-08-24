"""Constants for the SIP Phone integration."""

DOMAIN = "sip_phone"
PLATFORMS = ["sensor"]

CONF_COMMAND_TOPIC = "command_topic"
CONF_DEFAULT_ACCOUNT = "default_account"
CONF_EVENT_TOPIC = "event_topic"
CONF_NAME = "name"
CONF_SIP_DOMAIN = "sip_domain"

DEFAULT_COMMAND_TOPIC = "hasip/execute"
DEFAULT_EVENT_TOPIC = "hasip/state"
DEFAULT_NAME = "SIP Phone"
DEFAULT_SIP_ACCOUNT = 1

DATA_CLIENTS = "clients"
EVENT_CALL = f"{DOMAIN}.call_event"

SERVICE_ANSWER = "answer"
SERVICE_DIAL = "dial"
SERVICE_HANGUP = "hangup"
SERVICE_SEND_DTMF = "send_dtmf"

ATTR_DESTINATION = "destination"
ATTR_DIGITS = "digits"
ATTR_ENTRY_ID = "entry_id"
ATTR_METHOD = "method"
ATTR_RING_TIMEOUT = "ring_timeout"
ATTR_SIP_ACCOUNT = "sip_account"
ATTR_SIP_CODE = "sip_code"

DTMF_METHODS = ("in_band", "rfc2833", "sip_info")
