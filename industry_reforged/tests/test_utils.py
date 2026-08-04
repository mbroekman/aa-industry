# Standard Library
from unittest.mock import patch

# Third Party
import pytest

# AA Industry App
from industry_reforged.utils.fit_parser import parse_fit_text

from .factories import EveTypeFactory


@pytest.mark.django_db
class TestUtils:
    @patch("requests.post")
    def test_parse_fit_text_hull(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "inventory_types": [{"name": "Drake", "id": 123}]
        }
        EveTypeFactory(name="Drake", id=123)

        fit = "[Drake, My Fit]\nHeavy Missile Launcher II"
        items, unrec = parse_fit_text(fit)
        assert len(unrec) == 1
        assert "Heavy Missile Launcher II" in unrec

        drake_type = list(items.keys())[0]
        assert drake_type.name == "Drake"
        assert items[drake_type] == 1
