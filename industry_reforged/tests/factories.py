# Standard Library
from decimal import Decimal

# Third Party
import factory

# Eve Models
from eveuniverse.models import EveCategory, EveGroup, EveType

# Django
from django.contrib.auth.models import User

# Alliance Auth
from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo

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


class EveCategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EveCategory

    # Far above real EVE ids, so a random test category is never "Blueprint" (9)
    # or "Asteroid" (25), which the buyback treats specially.
    id = factory.Sequence(lambda n: n + 100000)
    name = factory.Sequence(lambda n: f"Category {n}")
    published = True


class EveGroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EveGroup

    # Far above real EVE group ids (see EveCategoryFactory).
    id = factory.Sequence(lambda n: n + 100000)
    name = factory.Sequence(lambda n: f"Group {n}")
    eve_category = factory.SubFactory(EveCategoryFactory)
    published = True


class EveTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EveType

    id = factory.Sequence(lambda n: n + 1)
    name = factory.Sequence(lambda n: f"Type {n}")
    published = True
    eve_group = factory.SubFactory(EveGroupFactory)


class EveCharacterFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EveCharacter

    character_id = factory.Sequence(lambda n: n + 90000000)
    character_name = factory.Sequence(lambda n: f"Character {n}")
    corporation_id = 1
    corporation_name = "Test Corp"


class EveCorporationInfoFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EveCorporationInfo

    corporation_id = factory.Sequence(lambda n: n + 98000000)
    corporation_name = factory.Sequence(lambda n: f"Corporation {n}")
    member_count = 1


class CharacterIndustryJobFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "industry_reforged.CharacterIndustryJob"

    character = factory.SubFactory(EveCharacterFactory)
    job_id = factory.Sequence(lambda n: n + 100000)
    activity_id = 1
    status = "active"


class CorporationIndustryJobFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "industry_reforged.CorporationIndustryJob"

    corporation = factory.SubFactory(EveCorporationInfoFactory)
    job_id = factory.Sequence(lambda n: n + 200000)
    activity_id = 1
    status = "active"


class CorpPricingConfigFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "industry_reforged.CorpPricingConfig"

    corporation = factory.SubFactory(EveCorporationInfoFactory)


class MemberOrderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "industry_reforged.MemberOrder"

    character = factory.SubFactory(EveCharacterFactory)
    total_price = factory.LazyFunction(lambda: Decimal("1000.00"))
    amount_paid = factory.LazyFunction(lambda: Decimal("0.00"))
    status = "REQUESTED"


class OrderItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "industry_reforged.OrderItem"

    order = factory.SubFactory(MemberOrderFactory)
    item_type = factory.SubFactory(EveTypeFactory)
    quantity = 1
    price_per_unit = factory.LazyFunction(lambda: Decimal("100.00"))


class ProductionTaskFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "industry_reforged.ProductionTask"

    item_type = factory.SubFactory(EveTypeFactory)
    quantity = 1
    activity_id = 1


class CorpWalletDivisionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "industry_reforged.CorpWalletDivision"

    corporation = factory.SubFactory(EveCorporationInfoFactory)
    division = factory.Sequence(lambda n: n + 1)
    name = factory.Sequence(lambda n: f"Division {n}")
    balance = factory.LazyFunction(lambda: Decimal("0.00"))


class BuybackProgramFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "industry_reforged.BuybackProgram"

    corporation = factory.SubFactory(EveCorporationInfoFactory)
    name = factory.Sequence(lambda n: f"Buyback Program {n}")
    is_active = True

    @factory.post_generation
    def facilities(self, create, extracted, **kwargs):
        """One drop-off facility by default; pass facilities=[...] to choose."""
        if not create:
            return
        self.facilities.set(
            extracted if extracted is not None else [IndustryFacilityFactory()]
        )


class BuybackWatchlistItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "industry_reforged.BuybackWatchlistItem"

    program = factory.SubFactory(BuybackProgramFactory)
    eve_type = factory.SubFactory(EveTypeFactory)
    blocks_submission = False


class BuybackContractFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "industry_reforged.BuybackContract"

    tracking_number = factory.Sequence(lambda n: f"BB-{n:08d}")
    program = factory.SubFactory(BuybackProgramFactory)
    character = factory.SubFactory(EveCharacterFactory)
    status = "PENDING"
    quoted_price = factory.LazyFunction(lambda: Decimal("1000.00"))


class BuybackContractItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "industry_reforged.BuybackContractItem"

    contract = factory.SubFactory(BuybackContractFactory)
    eve_type = factory.SubFactory(EveTypeFactory)
    quantity = 1
    unit_price = factory.LazyFunction(lambda: Decimal("100.00"))
    base_unit_price = factory.LazyAttribute(lambda o: o.unit_price)
