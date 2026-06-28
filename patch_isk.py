# Standard Library
import glob
import os
import re

template_dir = "/home/mbroekman/Development/aa-dev/working/aa-industry/industry_reforged/templates/industry_reforged"

files_to_patch = []
for file_path in glob.glob(f"{template_dir}/**/*.html", recursive=True):
    with open(file_path) as f:
        content = f.read()

    if "intcomma" in content:
        files_to_patch.append(file_path)

for file_path in files_to_patch:
    with open(file_path) as f:
        content = f.read()

    original = content

    # Replace when it has ISK explicitly
    content = re.sub(
        r"\|\s*floatformat:\d+\s*\|\s*intcomma\s*\}\}\s*ISK", "|eve_isk }}", content
    )
    content = re.sub(r"\|\s*intcomma\s*\}\}\s*ISK", "|eve_isk }}", content)

    # Specific cases without ISK text
    content = re.sub(
        r"job\.cost\|\s*floatformat:\d+\s*\|\s*intcomma\s*\}\}",
        "job.cost|eve_isk }}",
        content,
    )
    content = re.sub(
        r"entry\.total_isk\|\s*floatformat:\d+\s*\|\s*intcomma\s*\}\}",
        "entry.total_isk|eve_isk }}",
        content,
    )

    # Ensure {% load industry_tags %} is in the file if eve_isk is used
    if "eve_isk" in content and "{% load industry_tags %}" not in content:
        if "{% load" in content:
            content = re.sub(
                r"({% load [^}]+ %})", r"\1\n{% load industry_tags %}", content, count=1
            )
        else:
            content = "{% load industry_tags %}\n" + content

    if content != original:
        with open(file_path, "w") as f:
            f.write(content)
        print(f"Patched {os.path.basename(file_path)}")
