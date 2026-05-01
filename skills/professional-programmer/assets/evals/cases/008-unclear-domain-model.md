# 008 Unclear Domain Model

Business logic passes objects named `data`, `payload`, and `item` through invoice, refund, and shipment workflows.

New engineers confuse refund and shipment flows because names hide which business rule applies.
