# Compatibility

| Component | Supported contract |
| --- | --- |
| Domee integration | 0.1.0 preparation |
| Minimum Home Assistant | 2024.3.3 |
| Tested Home Assistant | 2024.3.3 and current stable |
| Snapshot schemas | 1 and 2 |
| Backend API prefix | `/api/v1/home-assistant` |

Within a supported schema, backend additions must be optional and ignored by
older clients. Existing identity and field semantics must not change
in-place. A future incompatible contract requires a new schema version.

Before the first public release, the compatibility policy is schemas 1 and 2.
After release, changes should maintain the current and previous supported
integration/backend pairing (N/N-1), with the exact matrix verified in CI.
