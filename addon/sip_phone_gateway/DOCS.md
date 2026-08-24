# SIP Phone Gateway

SIP Phone Gateway registers one or more Home Assistant extensions with a SIP server. It uses PJSIP for SIP signaling and media, and publishes command and call-state messages through MQTT for the SIP Phone HACS integration.

## Primary extension

Configure the **Primary SIP extension** section with values issued by the SIP server:

- **SIP registrar URI**: for example, `sip:pbx.local`.
- **Extension SIP URI**: for example, `sip:201@pbx.local`.
- **Extension username** and **Extension password**: the credentials for that extension.
- **Authentication realm**: usually `*` unless the SIP server specifies another realm.

The password control is intentionally a password field. It stays in the Home Assistant app configuration and is used only by the gateway to register the SIP extension.

## MQTT connection

Enable MQTT control and use the broker configured for Home Assistant. With the official Mosquitto app, `core-mosquitto` is the normal hostname. Set the same command and event topics in the SIP Phone HACS integration.

The defaults are:

```yaml
command_topic: hasip/execute
event_topic: hasip/state
```

## Add-on repository installation

In Home Assistant OS or Supervised, go to **Settings → Apps → App store → More → Repositories**, add this repository URL, then install **SIP Phone Gateway**. Configure and start the app before adding the SIP Phone HACS integration.

## Security

Use this gateway only with a trusted local SIP server and MQTT broker. Do not expose SIP, MQTT, or RTP ports to the public internet without authentication and transport protection.
