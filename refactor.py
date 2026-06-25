# Standard Library
import glob
import os
import re

template_dir = "industry_reforged/templates/industry_reforged/"

replacements = {
    "btn-amarr-solid": "btn-success",
    "btn-amarr": "btn-primary",
    "badge-amarr-solid": "bg-success",
    "badge-amarr": "bg-primary",
    "badge-glass": "bg-secondary",
    "glass-card": "border-secondary",
    "alert-glass": "alert-info",
    "text-amarr-gold": "text-primary",
    "text-amarr": "text-primary",
    "border-amarr": "border-primary",
}

regex_replacements = [
    # Remove inline style background colors related to amarr/glass
    (r'style="[^"]*background(?:-color)?:\s*rgba\([^)]+\)[^"]*"', ""),
    (r"style='[^']*background(?:-color)?:\s*rgba\([^)]+\)[^']*'", ""),
    # Specifically target the director_wallets style attribute: style="{% if selected_division_id == div.id %}border: 1px solid #d4af37 !important; background: rgba(212, 175, 55, 0.1);{% endif %}"
    (r'style="{% if [^}]+ %}border: [^;]+; background: rgba\([^)]+\);{% endif %}"', ""),
]

for filepath in glob.glob(os.path.join(template_dir, "*.html")):
    with open(filepath) as f:
        content = f.read()

    original = content
    for old, new in replacements.items():
        content = content.replace(old, new)

    for pattern, new in regex_replacements:
        content = re.sub(pattern, new, content)

    # specific inline fix for director_wallets DataTables JS
    content = content.replace(
        'style="background-color: rgba(255,255,255,0.05); color: #fff; border: 1px solid rgba(255,255,255,0.1);"',
        "",
    )

    if content != original:
        with open(filepath, "w") as f:
            f.write(content)
        print(f"Updated {filepath}")
