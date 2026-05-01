# 016 Singleton Temptation

A mutable singleton holds request-scoped user data to avoid passing context.

The service handles concurrent users and runs tests in parallel in CI.
