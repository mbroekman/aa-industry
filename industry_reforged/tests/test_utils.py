# Third Party
import pytest

# AA Industry App
from industry_reforged.utils.fit_parser import parse_fit_text


@pytest.mark.django_db
class TestUtils:
    def test_dummy_utils_import(self):
        assert parse_fit_text is not None
