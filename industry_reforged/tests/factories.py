# Third Party
import factory

# Django
from django.contrib.auth.models import User

# AA Industry App
from industry_reforged.models import IndustryFacility


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user_{n}")
    email = factory.Sequence(lambda n: f"user_{n}@example.com")


class IndustryFacilityFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = IndustryFacility

    facility_id = factory.Sequence(lambda n: n + 1000)
    name = factory.Sequence(lambda n: f"Facility {n}")
