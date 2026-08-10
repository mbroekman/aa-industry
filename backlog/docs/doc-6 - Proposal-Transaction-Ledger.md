---
id: doc-6
title: 'Proposal: Transaction Ledger'
type: specification
created_date: '2026-08-07 11:04'
updated_date: '2026-08-07 11:05'
---

# Transaction Ledger (History of Payments)

A proposal for tracking all manual payments (from members) and payouts (to builders) in a unified overview.

## Proposed Changes

### Models

Add a new `LedgerTransaction` model in `models/wallet.py`:

```python
class LedgerTransaction(models.Model):
    TRANSACTION_TYPES = (
        ("INCOME", _("Income (Member Payment)")),
        ("PAYOUT", _("Payout (Builder Batch)")),
        ("PROCUREMENT", _("Procurement (Buy Order)")),
    )

    date = models.DateTimeField(auto_now_add=True)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=20, decimal_places=2)

    # Who is this transaction with? (The Member / Builder)
    character = models.ForeignKey(
        EveCharacter,
        on_delete=models.SET_NULL,
        null=True,
        related_name="ledger_transactions",
    )

    # Which director registered the payment?
    director = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="processed_transactions",
    )

    reference = models.CharField(max_length=100)
    notes = models.TextField(blank=True, null=True)

    # Links to original objects
    member_order = models.ForeignKey(
        "MemberOrder",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
    )
    payout_batch = models.ForeignKey(
        "BuilderPayoutBatch",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
    )

    class Meta:
        ordering = ["-date"]
```

### Views & Logic

Modify the existing views in `director.py` to create `LedgerTransaction` records whenever a payment is made:

- `mark_order_paid`: Create an `INCOME` transaction.
- `mark_payout_batch_paid`: Create a `PAYOUT` transaction.
- `generate_payout_batch`: (Optional) We only record the transaction when it's marked as PAID.

### Frontend

- Add a new tab `Financial Ledger` to the Director Dashboard (`director_dashboard.html`).
- Display a DataTables view of all `LedgerTransaction` entries.
- Columns: Date, Type, Character, Reference, Amount (ISK formatted), Processed By, Notes.
- This will use Server-Side Processing for performance (similar to Orders/Tasks).

## Open Questions

> [!WARNING]
> Do we need to migrate *existing* payments? We can write a data migration that looks at all currently `PAID` MemberOrders and `PAID` BuilderPayoutBatches, and generates historical `LedgerTransaction` records for them using their `updated_at` / `paid_at` timestamps. Should I include this migration?

> [!NOTE]
> Are there any other types of transactions we should track now, aside from `INCOME` (Order Payments) and `PAYOUT` (Builder Payouts)?
