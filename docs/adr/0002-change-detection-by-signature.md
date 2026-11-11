# Detect member changes by payload signature, not API date filters

The Congress.gov list endpoint accepts `updateDate` and `fromDateTime`, but live probing showed `updateDate` is silently ignored (every value returns all 2696 members) and `fromDateTime` does not behave as a reliable incremental cursor. A date-driven incremental load would therefore miss updates.

We instead perform a full daily **Sweep** of current members (`currentMember=true`, ~539 records), compare each member's **Change Signature** against the last stored state, and fetch the per-member detail payload only when the signature indicates a change. The detail payload hash is authoritative; the list `updateDate` is a cheap pre-filter. This trades a slightly larger daily enumeration for correctness and self-healing behavior, which at ~539 members is negligible. A date-based cursor remains a possible optimization but is not trusted as the source of change truth.
