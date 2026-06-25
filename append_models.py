code = """
class CorpWalletDivision(models.Model):
    corporation = models.ForeignKey(
        EveCorporationInfo, on_delete=models.CASCADE, related_name="wallet_divisions"
    )
    division = models.IntegerField()
    name = models.CharField(max_length=100)
    balance = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Corp Wallet Division"
        verbose_name_plural = "Corp Wallet Divisions"
        unique_together = (("corporation", "division"),)

    def __str__(self):
        return f"{self.corporation.corporation_ticker} - {self.name} (Div {self.division})"


class CorpWalletJournal(models.Model):
    division = models.ForeignKey(
        CorpWalletDivision, on_delete=models.CASCADE, related_name="journal_entries"
    )
    journal_id = models.BigIntegerField()
    date = models.DateTimeField()
    ref_type = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    balance = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    reason = models.CharField(max_length=255, null=True, blank=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    first_party_id = models.BigIntegerField(null=True, blank=True)
    second_party_id = models.BigIntegerField(null=True, blank=True)
    tax = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    tax_receiver_id = models.BigIntegerField(null=True, blank=True)

    class Meta:
        verbose_name = "Corp Wallet Journal"
        verbose_name_plural = "Corp Wallet Journals"
        unique_together = (("division", "journal_id"),)
        ordering = ["-date"]

    def __str__(self):
        return f"Journal {self.journal_id} - {self.ref_type}"
"""

filepath = (
    "/home/mbroekman/Development/aa-dev/working/aa-industry/industry_reforged/models.py"
)
with open(filepath, "a") as f:
    f.write(code)

print("Appended models successfully.")
