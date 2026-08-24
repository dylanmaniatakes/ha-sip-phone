# SIP Phone for Home Assistant

SIP Phone makes a local SIP extension available to Home Assistant automations through native actions, events, and a call-status entity. The repository contains both a Home Assistant app that registers the extension and a HACS integration that provides the friendly Home Assistant control surface.

The project is designed for an on-premises PBX or SIP server that assigns extensions. SIP username and password are entered as protected fields in the **SIP Phone Gateway** app configuration. They are used only by the gateway; the HACS integration does not store or transmit them.

## Features

- `sip_phone.dial` accepts a simple extension (`201`), an address (`201@pbx.local`), or a full SIP URI.
- `sip_phone.hangup`, `sip_phone.answer`, and `sip_phone.send_dtmf` actions.
- `sip_phone.announce` to call an extension, play an optional chime, speak a message, and hang up.
- `sip_phone.connect_assist` to answer a call to the Home Assistant extension and bridge it to Assist.
- A `sensor` entity for each configured extension with `idle`, `ringing`, or `connected` state.
- `sip_phone.call_event` events containing the SIP gateway's call payload.
- Protected text inputs for registrar URI, extension URI, username, and password in the SIP gateway app.
- A HACS config flow with text fields for the server address, account slot, and MQTT topics.

## Requirements

1. Home Assistant OS or Supervised to use the included SIP Phone Gateway app. Home Assistant Container or Core can use a separately deployed compatible gateway.
2. The MQTT integration connected to a local broker.
3. An extension username, password, and SIP registrar URI issued by the local SIP server.

The included gateway is based on the Apache-2.0 licensed [ha-sip](https://github.com/arnonym/ha-plugins) PJSIP implementation, updated with direct password fields and a dedicated MQTT section. The default topics are:

```yaml
command_topic: hasip/execute
event_topic: hasip/state
```

Configure **SIP Phone Gateway** first. In its **Primary SIP extension** section, enter the registrar URI, extension URI, extension username, and extension password. In **Home Assistant MQTT connection**, enter the broker credentials and keep the topics matched to the HACS integration. Full gateway configuration is in [DOCS.md](/Users/ticnitsi/Documents/ha-sip-phone/addon/sip_phone_gateway/DOCS.md).

## Installation

1. For Home Assistant OS or Supervised, add this repository in **Settings → Apps → App store → More → Repositories**, then install and start **SIP Phone Gateway**. It presents text inputs for the SIP registrar, extension username, and password.
2. In HACS, add this repository as a custom repository of type **Integration**, download **SIP Phone**, and restart Home Assistant.
3. Go to **Settings → Devices & services → Add integration**, select **SIP Phone**, and enter the server address, gateway account slot, and matching MQTT topics. The account slot is a text field, not a slider.

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

## Call announcements and Chime TTS

`sip_phone.announce` calls the destination, plays an optional chime first, speaks the message through the gateway's configured TTS engine, and hangs up after playback.

```yaml
action: sip_phone.announce
data:
  destination: "201"
  chime_file: /media/chime_tts/custom_chimes/bell.mp3
  message: "The front door has opened."
```

The gateway can play `.wav` and `.mp3` files from `/media`. Chime TTS supports custom chimes in Home Assistant's media folder, so a Chime TTS chime path can be used directly as `chime_file`. Chime TTS itself is not required for spoken SIP announcements; the gateway uses the TTS engine configured in the SIP Phone Gateway app.

## Home Assistant Assist over SIP

To make a call to the Home Assistant extension and talk with Assist:

1. Set up Home Assistant's **Voice over IP** integration with a dedicated SIP username and a local port different from the SIP Phone Gateway port (for example, `5070`). Enable incoming calls for the resulting device.
2. In the SIP Phone integration options, set **Home Assistant Assist SIP URI** to that endpoint, such as `sip:assist@192.168.1.10:5070`.
3. Create an automation that connects each incoming SIP call to Assist:

```yaml
trigger:
  - trigger: event
    event_type: sip_phone.call_event
    event_data:
      event: incoming_call
action:
  - action: sip_phone.connect_assist
    data:
      destination: "{{ trigger.event.data.internal_id }}"
```

Use a condition on `trigger.event.data.parsed_remote_uri` if only selected callers should reach Assist. `connect_assist` answers the call, dials the configured Home Assistant Voice over IP endpoint, waits for it to answer, then bridges the two audio streams.

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

The **SIP Phone Gateway** app owns extension registration, codec negotiation, RTP media, and credentials; the **SIP Phone** HACS integration provides Home Assistant-native control through MQTT. This separates credential-bearing SIP transport from the automation UI and allows Container and Core installations to use a separately deployed compatible gateway.

The status sensor reflects gateway events. It is `idle` until an event is received after Home Assistant starts, so it is a call indicator rather than a SIP registration-health check.

## License

Apache-2.0. This project interoperates with, but does not include code from, the separately licensed ha-sip project.
