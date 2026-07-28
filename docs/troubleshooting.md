# Troubleshooting

- **Setup cannot connect:** verify the backend URL is HTTPS, reachable from the
  Home Assistant host, and has no extra API suffix.
- **Authentication fails or reauth appears:** create a new integration token for
  the same Domee backend installation and account, then complete reauthentication.
- **Entities are unavailable:** confirm the backend is online and has current
  device telemetry. A newly reconnected backend intentionally waits for a
  physical device confirmation.
- **A command button has no visible state:** IR/RF buttons are stateless by
  design.
- **A switch command does not change state:** the physical device must report the
  new state. Check backend/device connectivity rather than assuming command
  delivery changed the relay.

Enable debug logging for `custom_components.domee` only while investigating.
Never include integration tokens in shared logs.
