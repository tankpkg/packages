# 006 Bad API Design

An API requires callers to pass five positional strings and a boolean flag that changes validation behavior.

Several call sites already pass the strings in different orders during tests, making misuse plausible.
