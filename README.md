# Domee for Home Assistant

Domee connects a Home Assistant installation to a Domee backend account. It
supports physical Wi-Fi switch channels, central-hub connectivity and diagnostic
sensors, and stateless IR/RF commands exposed as buttons.

## Requirements

- Home Assistant 2024.3.3 or newer.
- A reachable Domee backend that supports snapshot schemas 1 or 2.
- A Domee Home Assistant integration token.

## Installation

This repository is being prepared for distribution and has not been published to
HACS. For local validation, copy `custom_components/domee` into the
`custom_components` directory of your Home Assistant configuration, restart Home
Assistant, then add **Domee** from **Settings ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ Devices & services**.

The public repository is
[sil-main-coo/domee-home-assistant](https://github.com/sil-main-coo/domee-home-assistant).
HACS installation will be documented after the first release is published.

## Configuration

Create a dedicated Home Assistant integration token using the authenticated
Domee backend token API. Store the token securely; it grants access to the
devices shared with that account. In the config flow, enter the HTTPS backend URL
and the integration token.

Power shown for Wi-Fi switches comes only from reported device telemetry. Sending
a command does not fabricate a successful physical state. IR/RF commands are
stateless and therefore appear as buttons.

## Supported entities

- Stateful physical Wi-Fi switch channels.
- Central-hub connectivity.
- Central-hub diagnostic sensors.
- Stateless IR/RF commands and scripts.

## Known limitations

- IR/RF devices do not expose fake power state.
- Home Assistant reads backend snapshots on a polling interval; cached,
  authoritative telemetry can lag the physical device.
- There is no push, SSE, or WebSocket update channel.

See [troubleshooting](docs/troubleshooting.md) for recovery steps and
[compatibility](docs/compatibility.md) for the supported contract.

## License

Licensed under your choice of [MIT](LICENSE-MIT) or [Apache-2.0](LICENSE-APACHE).
