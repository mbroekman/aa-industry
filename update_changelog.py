import re

with open("CHANGELOG.md", "r") as f:
    content = f.read()

new_release = """## v0.14.3 (2026-10-01)

### Fix

- **ui**: update misleading empty inventory text to reference facilities instead of hangars

"""

content = re.sub(r'^(# Change Log\s*\n\nAll notable changes to this project will be documented in this file.\n\nThe format is based on \[Keep a Changelog\]\(http://keepachangelog.com/\)\n)', r'\1\n' + new_release, content)

with open("CHANGELOG.md", "w") as f:
    f.write(content)
