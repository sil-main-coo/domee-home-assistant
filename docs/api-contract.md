# Domee Home Assistant API contract

All endpoints use the `/api/v1/home-assistant` prefix and authenticate with an
integration token in `Authorization: Bearer <token>`. HTTP 401 means the token is
invalid or revoked and starts Home Assistant reauthentication. Transport errors
and malformed responses are not authentication failures.

Successful responses use an envelope containing `data`.

## Snapshot

`GET /snapshot` returns the account-visible Home Assistant model. The data object
contains `schemaVersion`, `backendInstanceId`, account identity, normalized hubs,
devices, entities, and scripts. Schema versions 1 and 2 are supported.
`backendInstanceId` and the account ID form the stable config-entry identity.
Unknown additive fields are ignored; malformed required identity or an
unsupported schema invalidates the update.

The snapshot exposes normalized data only. Reported physical telemetry is the
authority for switch state; issuing a command does not imply physical success.

## Commands

- `POST /commands` invokes a stateless hub/button command.
- `POST /scripts/{scriptId}/execute` invokes a Domee script.
- `POST /devices/{deviceId}/commands` accepts a domain command such as
  `{"capability":"power","channel":1,"value":true,"requestId":"..."}`.

`requestId` identifies command delivery through the software path. A successful
HTTP response confirms acceptance/delivery, not acknowledgement by the physical
device. A later reported snapshot confirms physical state.
