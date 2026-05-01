# 003 Shared Mutable State

Several concurrent jobs update a global in-memory `currentStatus` object and tests pass only when run serially.

Parallel workers process separate accounts, so cross-request contamination would be a production incident.
