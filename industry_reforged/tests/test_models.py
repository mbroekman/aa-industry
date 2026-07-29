# Third Party
import pytest

from .factories import IndustryFacilityFactory


@pytest.mark.django_db
class TestIndustryFacilityModel:
    def test_create_facility(self):
        facility = IndustryFacilityFactory(name="Test Facility")
        assert facility.name == "Test Facility"
        assert facility.facility_id is not None
