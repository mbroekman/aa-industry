filepath = "/home/mbroekman/Development/aa-dev/working/aa-industry/README.md"
with open(filepath) as f:
    content = f.read()

# Update package name
content = content.replace("aa-industry", "aa-industry-reforged")

# Add Corporate Wallets feature
content = content.replace(
    "- **Director Control Panel**: Complete ERP solution for directors to manage orders, prioritize tasks, analyze missing stock, and set rules for Material Efficiency and Prices.",
    "- **Director Control Panel**: Complete ERP solution for directors to manage orders, prioritize tasks, analyze missing stock, and set rules for Material Efficiency and Prices.\n- **Corporate Wallets**: Track ISK balances and journal transactions across all 7 corporate wallet divisions.",
)

# Add wallet scope
content = content.replace(
    '- **`esi-corporations.read_structures.v1`**: Required for the Director Control Panel to discover and resolve names for structures owned by the corporation. Directors grant this via the "Add Corporate Token" button.',
    '- **`esi-corporations.read_structures.v1`**: Required for the Director Control Panel to discover and resolve names for structures owned by the corporation. Directors grant this via the "Add Corporate Token" button.\n- **`esi-wallet.read_corporation_wallets.v1`**: Required to track corporate wallet balances and journal transactions. Directors grant this via the "Add Corporate Token" button.',
)

# Remove manual sync config note
content = content.replace(
    "*Note: For Corporate Syncs, an Admin must link the Director character in the Django Admin interface under **Corporation Sync Configuration**.*",
    "*Note: Corporate Sync Configuration is automatically created when a Director clicks the 'Add Corporate Token' button.*",
)

# Add wallet sync task to celerybeat
celery_block_old = """CELERYBEAT_SCHEDULE["industry_pull_market_data"] = {
    "task": "industry_reforged.tasks.task_pull_market_data",
    "schedule": crontab(hour="11", minute="30"),  # Around EVE Downtime
}"""

celery_block_new = """CELERYBEAT_SCHEDULE["industry_pull_market_data"] = {
    "task": "industry_reforged.tasks.task_pull_market_data",
    "schedule": crontab(hour="11", minute="30"),  # Around EVE Downtime
}

CELERYBEAT_SCHEDULE["industry_sync_corp_wallets"] = {
    "task": "industry_reforged.tasks.task_sync_corp_wallets",
    "schedule": crontab(minute="*/30"),
}"""

content = content.replace(celery_block_old, celery_block_new)

with open(filepath, "w") as f:
    f.write(content)

print("README.md updated.")
