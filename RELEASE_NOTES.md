# Domee v0.1.0

The first Domee Home Assistant release includes:

- Domee config flow with stable backend/account identity.
- Authoritative physical Wi-Fi switch entities.
- Central hub connectivity and diagnostic sensors.
- Stateless IR/RF commands and script buttons.
- Token reauthentication and strict snapshot schema handling.
- Minimum Home Assistant version 2024.3.3.

Known limitations:

- IR/RF state is not fabricated.
- Updates are polling/cache based.
- There is no push, SSE, or WebSocket Home Assistant update channel.
- A compatible Domee backend is required.