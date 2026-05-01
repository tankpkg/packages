# 022 Security Convenience

An admin endpoint skips authorization in staging and the same flag can reach production.

The staging flag is read from the same configuration path used by production deploys.
