# Standard Library
import json

# Third Party
import requests


def generate():
    print("Fetching planetSchematics.json...")
    r1 = requests.get("https://sde.zzeve.com/planetSchematics.json")
    schematics = r1.json()

    print("Fetching planetSchematicsTypeMap.json...")
    r2 = requests.get("https://sde.zzeve.com/planetSchematicsTypeMap.json")
    typemap = r2.json()

    out = {}
    for sch in schematics:
        sid = sch["schematicID"]
        out[sid] = {
            "name": sch["schematicName"],
            "cycle_time": sch["cycleTime"],
            "inputs": {},
            "outputs": {},
        }

    for tm in typemap:
        sid = tm["schematicID"]
        tid = tm["typeID"]
        qty = tm["quantity"]
        is_in = tm["isInput"]
        if is_in == 1 or is_in is True:
            out[sid]["inputs"][tid] = qty
        else:
            out[sid]["outputs"][tid] = qty

    with open("industry_reforged/utils/pi_schematics.py", "w", encoding="utf-8") as f:
        f.write("# Auto-generated from EVE SDE\n\n")
        f.write("PI_SCHEMATICS = \\\n")
        f.write(json.dumps(out, indent=4))
        f.write("\n")

    print("Generated industry_reforged/utils/pi_schematics.py")


if __name__ == "__main__":
    generate()
