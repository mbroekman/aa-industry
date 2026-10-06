import re

with open('industry_reforged/templates/industry_reforged/manage_facility.html', 'r') as f:
    content = f.read()

js_code = """
    function filterRigs() {
        const typeIdInput = document.getElementById("id_type_id");
        if (!typeIdInput) return;
        const typeId = parseInt(typeIdInput.value);
        
        let allowedSize = "";
        if ([35832, 35825, 35835].includes(typeId)) {
            allowedSize = " M-";
        } else if ([35833, 35826, 35836].includes(typeId)) {
            allowedSize = " L-";
        } else if ([35834, 35827].includes(typeId)) {
            allowedSize = " XL-";
        }
        
        const rigSelects = document.querySelectorAll("select[id^='id_rigs-'][id$='-rig']");
        
        rigSelects.forEach(select => {
            Array.from(select.options).forEach(opt => {
                if (opt.value === "") return;
                const text = opt.text;
                if (allowedSize === "") {
                    opt.disabled = false;
                    opt.style.display = "";
                } else {
                    if (text.includes(allowedSize)) {
                        opt.disabled = false;
                        opt.style.display = "";
                    } else {
                        opt.disabled = true;
                        opt.style.display = "none";
                    }
                }
            });
            
            if (select.selectedIndex > 0 && select.options[select.selectedIndex].disabled) {
                select.value = "";
            }
        });
    }
"""

content = content.replace("function updateSecuritySpace(systemId) {", js_code + "\n    function updateSecuritySpace(systemId) {")

content = content.replace(
    'document.getElementById("id_solar_system_id").value = systemId;\n                    updateSecuritySpace(systemId);',
    'document.getElementById("id_solar_system_id").value = systemId;\n                    updateSecuritySpace(systemId);\n                    filterRigs();'
)

content = content.replace(
    "totalForms.value = formCount + 1;",
    "totalForms.value = formCount + 1;\n                filterRigs();"
)

content = content.replace(
    'document.addEventListener("DOMContentLoaded", function() {',
    'document.addEventListener("DOMContentLoaded", function() {\n        filterRigs();\n        \n        const typeIdInput = document.getElementById("id_type_id");\n        if (typeIdInput) {\n            typeIdInput.addEventListener("change", filterRigs);\n            typeIdInput.addEventListener("input", filterRigs);\n        }'
)

with open('industry_reforged/templates/industry_reforged/manage_facility.html', 'w') as f:
    f.write(content)

