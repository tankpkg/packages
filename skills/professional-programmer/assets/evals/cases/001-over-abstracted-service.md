# 001 Over-Abstracted Service

A payment service has one implementation but introduces `AbstractPaymentProviderFactoryStrategyAdapter` and four layers of pass-through interfaces. User behavior is simple: capture a payment and record the result.
