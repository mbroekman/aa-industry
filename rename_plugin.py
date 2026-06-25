# Standard Library
import os

BASE_DIR = "/home/mbroekman/Development/aa-dev/working/aa-industry"

# 1. Rename directories
old_module = os.path.join(BASE_DIR, "industry_reforged")
new_module = os.path.join(BASE_DIR, "industry_reforged")

if os.path.exists(old_module):
    print("Renaming industry/ to industry_reforged/")
    os.rename(old_module, new_module)

old_templates = os.path.join(new_module, "templates", "industry_reforged")
new_templates = os.path.join(new_module, "templates", "industry_reforged")
if os.path.exists(old_templates):
    print("Renaming templates/industry/ to templates/industry_reforged/")
    os.rename(old_templates, new_templates)

old_static = os.path.join(new_module, "static", "industry_reforged")
new_static = os.path.join(new_module, "static", "industry_reforged")
if os.path.exists(old_static):
    print("Renaming static/industry/ to static/industry_reforged/")
    os.rename(old_static, new_static)

# 2. String replacements mapping
REPLACEMENTS = {
    # pyproject.toml
    'name = "aa-industry-reforged"': 'name = "aa-industry-reforged"',
    'version.path = "industry_reforged/__init__.py"': 'version.path = "industry_reforged/__init__.py"',
    'build.include = [\n    "/industry",\n]': 'build.include = [\n    "/industry_reforged",\n]',
    # Python imports & references
    "from industry_reforged import": "from industry_reforged import",
    "from industry_reforged.": "from industry_reforged.",
    "import industry\n": "import industry_reforged\n",
    "reverse('industry_reforged:": "reverse('industry_reforged:",
    'reverse("industry_reforged:': 'reverse("industry_reforged:',
    'app_name = "industry_reforged"': 'app_name = "industry_reforged"',
    "app_name = 'industry_reforged'": "app_name = 'industry_reforged'",
    'name = "industry_reforged"': 'name = "industry_reforged"',
    "name = 'industry_reforged'": "name = 'industry_reforged'",
    'label = "industry_reforged"': 'label = "industry_reforged"',
    "label = 'industry_reforged'": "label = 'industry_reforged'",
    '"industry_reforged.tasks': '"industry_reforged.tasks',
    "'industry_reforged.tasks": "'industry_reforged.tasks",
    'permission_required("industry_reforged.': 'permission_required("industry_reforged.',
    "permission_required('industry_reforged.": "permission_required('industry_reforged.",
    'has_perm("industry_reforged.': 'has_perm("industry_reforged.',
    "has_perm('industry_reforged.": "has_perm('industry_reforged.",
    # Templates
    "{% url 'industry_reforged:": "{% url 'industry_reforged:",
    '{% url "industry_reforged:': '{% url "industry_reforged:',
    '{% extends "industry_reforged/': '{% extends "industry_reforged/',
    "{% extends 'industry_reforged/": "{% extends 'industry_reforged/",
    '{% include "industry_reforged/': '{% include "industry_reforged/',
    "{% include 'industry_reforged/": "{% include 'industry_reforged/",
    "{% static 'industry_reforged/": "{% static 'industry_reforged/",
    '{% static "industry_reforged/': '{% static "industry_reforged/',
    "perms.industry_reforged": "perms.industry_reforged_reforged",
    # Markdown docs / README (optional but good)
    '"industry_reforged.tasks.update_character_jobs"': '"industry_reforged.tasks.update_character_jobs"',
    '"industry_reforged.tasks.update_corporation_jobs"': '"industry_reforged.tasks.update_corporation_jobs"',
    '"industry_reforged.tasks.update_character_pi"': '"industry_reforged.tasks.update_character_pi"',
    '"industry_reforged.tasks.task_sync_corp_inventory"': '"industry_reforged.tasks.task_sync_corp_inventory"',
    '"industry_reforged"': '"industry_reforged"',  # Risky, let's only do it for INSTALLED_APPS
}

# Add a specific one for INSTALLED_APPS in README
REPLACEMENTS['       "industry_reforged",'] = '       "industry_reforged",'


def process_file(filepath):
    try:
        with open(filepath, encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return  # Skip binaries etc

    original = content
    for old, new in REPLACEMENTS.items():
        content = content.replace(old, new)

    if content != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Updated: {filepath}")


for root, dirs, files in os.walk(BASE_DIR):
    if ".git" in root or "venv" in root or "dist" in root or "__pycache__" in root:
        continue
    for file in files:
        if file.endswith((".py", ".html", ".toml", ".md", ".txt")):
            process_file(os.path.join(root, file))

print("Done!")
