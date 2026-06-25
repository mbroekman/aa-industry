filepath = (
    "/home/mbroekman/Development/aa-dev/working/aa-industry/industry_reforged/views.py"
)
with open(filepath) as f:
    content = f.read()

content = content.replace('"industry/', '"industry_reforged/')

with open(filepath, "w") as f:
    f.write(content)
print("Fixed views.py")
