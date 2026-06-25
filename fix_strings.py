files_to_fix = [
    "/home/mbroekman/Development/aa-dev/working/aa-industry/industry_reforged/views.py",
    "/home/mbroekman/Development/aa-dev/working/aa-industry/industry_reforged/auth_hooks.py",
]

for filepath in files_to_fix:
    with open(filepath) as f:
        content = f.read()

    content = content.replace('"industry:', '"industry_reforged:')

    with open(filepath, "w") as f:
        f.write(content)
    print(f"Fixed {filepath}")
