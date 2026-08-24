# SIP Phone for Home Assistant

SIP Phone makes a local SIP extension available to Home Assistant automations through native actions, events, and a call-status entity. It is a HACS custom integration and uses an MQTT-enabled SIP gateway to handle SIP registration and media.

The integration is designed for an on-premises PBX or SIP server that assigns extensions. It never sends SIP credentials to Home Assistant; those remain in the SIP gateway configuration.

## Features

- `sip_phone.dial` accepts a simple extension (`201`), an address (`201@pbx.local`), or a full SIP URI.
- `sip_phone.hangup`, `sip_phone.answer`, and `sip_phone.send_dtmf` actions.
- A `sensor` entity for each configured extension with `idle`, `ringing`, or `connected` state.
- `sip_phone.call_event` events containing the SIP gateway's call payload.
- A config flow that asks only for a friendly name, SIP server address, account number, and MQTT topics.

## Requirements

1. Home Assistant with the MQTT integration connected to a local broker.
2. A SIP gateway registered as an extension on the local SIP server.
3. Gateway MQTT command and state events enabled.

[ha-sip](https://github.com/arnonym/ha-plugins) is a compatible Home Assistant add-on and supplies the SIP/PJSIP runtime. Enable its MQTT feature with matching command and state topics. The default topics used by both projects are:

```yaml
command_topic: hasip/execute
event_topic: hasip/state
```

For ha-sip, add this to `sip_global.global_options`, alongside the correct local broker details:

```text
--enable-mqtt --mqtt-address core-mosquitto --mqtt-port 1883 --mqtt-topic hasip/execute --mqtt-state-topic hasip/state
```

Configure SIP credentials only in the gateway. SIP Phone selects the configured account by number and does not duplicate or store its password.

## Installation

1. In HACS, add this repository as a custom repository of type **Integration**.
2. Download **SIP Phone** and restart Home Assistant.
3. Go to **Settings → Devices & services → Add integration**, select **SIP Phone**, and enter the SIP server address and account number used by the gateway.

## Automation actions

The Actions picker exposes typed fields for all actions. An outgoing extension call can be as small as:

```yaml
action: sip_phone.dial
data:
  destination: "201"
  ring_timeout: 20
```

`201` becomes `sip:201@<configured SIP server>`. A full URI is preserved:

```yaml
action: sip_phone.dial
data:
  destination: "sip:201@pbx.local"
```

For more than one SIP Phone entry, include the entry ID shown on the integration page:

```yaml
action: sip_phone.dial
data:
  entry_id: 0123456789abcdef
  destination: "201"
```

Send DTMF after a connected call:

```yaml
action: sip_phone.send_dtmf
data:
  destination: "201"
  digits: "123#"
  method: rfc2833
```

## Incoming calls

Gateway events are re-emitted locally as `sip_phone.call_event`, eliminating separate webhook IDs:

```yaml
trigger:
  - platform: event
    event_type: sip_phone.call_event
    event_data:
      event: incoming_call
action:
  - action: persistent_notification.create
    data:
      title: Incoming SIP call
      message: "{{ trigger.event.data.parsed_remote_uri }} is calling"
```

To answer the call, use the event's `internal_id`:

```yaml
action: sip_phone.answer
data:
  destination: "{{ trigger.event.data.internal_id }}"
```

## Design and limits

This repository is intentionally a HACS integration, not a second SIP media stack. The SIP gateway owns extension registration, codec negotiation, RTP media, and credentials; SIP Phone provides Home Assistant-native control through MQTT. This supports Home Assistant OS, Supervised, Container, and Core installations as long as the compatible gateway is reachable.

The status sensor reflects gateway events. It is `idle` until an event is received after Home Assistant starts, so it is a call indicator rather than a SIP registration-health check.

## License

Apache-2.0. This project interoperates with, but does not include code from, the separately licensed ha-sip project.
