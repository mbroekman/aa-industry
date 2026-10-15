# Third Party
import pytest

# AA Industry App
from industry_reforged.utils.inventory_parser import parse_inventory_paste

from .factories import EveTypeFactory


@pytest.mark.django_db
class TestParseInventoryPaste:
    def test_standard_six_column_paste(self):
        tritanium = EveTypeFactory(name="Tritanium")
        pyerite = EveTypeFactory(name="Pyerite")
        text = (
            "Tritanium\t1000\tMinerals\tMaterial\tHigh\t10\n"
            "Pyerite\t500\tMinerals\tMaterial\tHigh\t5\n"
        )
        parsed, unrecognized = parse_inventory_paste(text)
        assert parsed == {tritanium: 1000, pyerite: 500}
        assert unrecognized == []

    def test_two_column_minimal_paste(self):
        tritanium = EveTypeFactory(name="Tritanium")
        parsed, unrecognized = parse_inventory_paste("Tritanium\t250")
        assert parsed == {tritanium: 250}
        assert unrecognized == []

    def test_single_column_defaults_to_qty_one(self):
        tritanium = EveTypeFactory(name="Tritanium")
        parsed, unrecognized = parse_inventory_paste("Tritanium")
        assert parsed == {tritanium: 1}

    def test_thousands_separated_quantity_comma(self):
        tritanium = EveTypeFactory(name="Tritanium")
        parsed, _ = parse_inventory_paste("Tritanium\t1,234")
        assert parsed == {tritanium: 1234}

    def test_thousands_separated_quantity_dot(self):
        tritanium = EveTypeFactory(name="Tritanium")
        parsed, _ = parse_inventory_paste("Tritanium\t1.234")
        assert parsed == {tritanium: 1234}

    def test_trailing_singleton_marker_stripped(self):
        rifter = EveTypeFactory(name="Rifter")
        parsed, _ = parse_inventory_paste("Rifter*\t1")
        assert parsed == {rifter: 1}

    def test_duplicate_item_name_quantities_summed(self):
        tritanium = EveTypeFactory(name="Tritanium")
        text = "Tritanium\t100\n" "Tritanium\t50\n"
        parsed, _ = parse_inventory_paste(text)
        assert parsed == {tritanium: 150}

    def test_blank_lines_and_crlf_ignored(self):
        tritanium = EveTypeFactory(name="Tritanium")
        text = "\r\nTritanium\t10\r\n\r\n   \r\n"
        parsed, _ = parse_inventory_paste(text)
        assert parsed == {tritanium: 10}

    def test_unrecognized_item_returned_not_raised(self):
        parsed, unrecognized = parse_inventory_paste("Totally Fake Item\t1")
        assert parsed == {}
        assert unrecognized == ["Totally Fake Item"]

    def test_compressed_ore_name_resolves(self):
        compressed = EveTypeFactory(name="Compressed Veldspar")
        parsed, unrecognized = parse_inventory_paste("Compressed Veldspar\t42")
        assert parsed == {compressed: 42}
        assert unrecognized == []

    def test_empty_input_returns_empty(self):
        parsed, unrecognized = parse_inventory_paste("")
        assert parsed == {}
        assert unrecognized == []

    def test_blueprint_name_resolves_like_any_other_type(self):
        """Blueprint exclusion is a program/watchlist concern, not a parsing one -
        the parser must resolve a blueprint-named EveType the same as any other."""
        bpc = EveTypeFactory(name="Rifter Blueprint")
        parsed, unrecognized = parse_inventory_paste("Rifter Blueprint\t1")
        assert parsed == {bpc: 1}
        assert unrecognized == []
