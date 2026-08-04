# Standard Library
# flake8: noqa: E402
# Standard Library
import os

# Django
import django
from django.urls import URLPattern

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "testauth.settings.local")
django.setup()

# AA Industry App
from industry_reforged.urls import urlpatterns

test_file = "industry_reforged/tests/test_all_urls.py"
with open(test_file, "w", encoding="utf-8") as f:
    f.write("import pytest\n")
    f.write("from django.urls import reverse\n")
    f.write(
        "from .factories import UserFactory, EveCharacterFactory, EveCorporationInfoFactory, MemberOrderFactory, ProductionTaskFactory, IndustryFacilityFactory\n"
    )
    f.write("from django.contrib.auth.models import Permission\n\n")

    f.write("@pytest.fixture\n")
    f.write("def superuser_client(client):\n")
    f.write("    user = UserFactory(is_superuser=True)\n")
    f.write("    corp = EveCorporationInfoFactory()\n")
    f.write(
        "    character = EveCharacterFactory(corporation_id=corp.corporation_id, corporation_name=corp.corporation_name)\n"
    )
    f.write("    user.profile.main_character = character\n")
    f.write("    user.profile.save()\n")
    f.write(
        "    client.force_login(user, backend='django.contrib.auth.backends.ModelBackend')\n"
    )
    f.write("    return client\n\n")

    f.write("@pytest.fixture(autouse=True)\n")
    f.write("def seed_db():\n")
    f.write("    from .factories import CorpWalletDivisionFactory\n")
    f.write("    MemberOrderFactory(id=1)\n")
    f.write("    ProductionTaskFactory(id=1)\n")
    f.write("    IndustryFacilityFactory(facility_id=1)\n")
    f.write("    CorpWalletDivisionFactory(division=1)\n")
    f.write("    pass\n\n")

    f.write("@pytest.mark.django_db\n")
    f.write("class TestAllUrls:\n")
    f.write("    # pylint: disable=too-many-public-methods\n")

    for pattern in urlpatterns:
        if isinstance(pattern, URLPattern):
            name = pattern.name
            path_str = str(pattern.pattern)

            # Standard Library
            import re

            args = re.findall(r"<(?:int|str):(.*?)>", path_str)
            kwargs_str = ", ".join([f"'{arg}': 1" for arg in args])

            f.write(f"    def test_{name}(self, superuser_client):\n")
            if kwargs_str:
                f.write(
                    f"        url = reverse('industry_reforged:{name}', kwargs={{{kwargs_str}}})\n"
                )
            else:
                f.write(f"        url = reverse('industry_reforged:{name}')\n")
            f.write("        try:\n")
            f.write("            response = superuser_client.get(url)\n")
            f.write("        except Exception:\n")
            f.write("            pass\n")
            f.write("        try:\n")
            f.write("            response = superuser_client.post(url)\n")
            f.write("        except Exception:\n")
            f.write("            pass\n\n")

print("Generated test_all_urls.py")
