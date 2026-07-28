# Domee for Home Assistant

Domee connects a Home Assistant installation to a Domee backend account. It
supports physical Wi-Fi switch channels, central-hub connectivity and diagnostic
sensors, and stateless IR/RF commands exposed as buttons.

## Requirements

- Home Assistant 2024.3.3 or newer.
- A reachable Domee backend that supports snapshot schemas 1 or 2.
- A Domee Home Assistant integration token.

## Installation

The public repository is
[`sil-main-coo/domee-home-assistant`](https://github.com/sil-main-coo/domee-home-assistant).
It is supported as a HACS custom repository; it is not currently listed in the
HACS default store.

### HACS custom repository

1. Open HACS and add `https://github.com/sil-main-coo/domee-home-assistant` as
   an **Integration** custom repository.
2. Find **Domee**, select release `v0.1.0`, and install it.
3. Restart Home Assistant.
4. Add **Domee** from **Settings > Devices & services**.

If HACS cached repository data before a new release appeared, refresh HACS or
reload the repository and try again.

### Manual installation

1. Download `domee.zip` from the
   [v0.1.0 release](https://github.com/sil-main-coo/domee-home-assistant/releases/tag/v0.1.0).
2. Extract its root-level files into
   `<Home Assistant config>/custom_components/domee`.
3. Restart Home Assistant and add **Domee** from
   **Settings > Devices & services**.

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

## Reinstall and rollback

Reinstalling the same release preserves config-entry, device, and entity
identities. Uninstalling removes the integration code but does not revoke the
backend token; revoke it separately when access is no longer needed. Starting
with a future release, rollback means reinstalling the previous published
release after checking its compatibility matrix. No synthetic pre-0.1.0 release
exists.

## License

Licensed under your choice of [MIT](LICENSE-MIT) or [Apache-2.0](LICENSE-APACHE).