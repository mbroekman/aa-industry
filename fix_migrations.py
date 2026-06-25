# Standard Library
import glob
import os

migrations_dir = "/home/mbroekman/Development/aa-dev/working/aa-industry/industry_reforged/migrations"

for filepath in glob.glob(os.path.join(migrations_dir, "*.py")):
    with open(filepath) as f:
        content = f.read()

    if 'to="industry.' in content or "to='industry." in content:
        content = content.replace('to="industry.', 'to="industry_reforged.')
        content = content.replace("to='industry.", "to='industry_reforged.")

        with open(filepath, "w") as f:
            f.write(content)
        print(f"Fixed {filepath}")
