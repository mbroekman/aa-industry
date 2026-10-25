# AA Industry App
from industry_reforged.utils.buyback_matching import (
    BuybackContractExpectation,
    ExpectedItem,
    extract_tracking_number,
    match_contract,
)


def _expectation(**overrides):
    defaults = {
        "tracking_number": "BB-ABCD1234",
        "expected_items": [ExpectedItem(type_id=34, quantity=1000)],
        "expected_price": 1000.0,
        "expected_location_id": 60003760,
        "expected_receiver_id": 98000001,
    }
    defaults.update(overrides)
    return BuybackContractExpectation(**defaults)


def _esi_contract(**overrides):
    defaults = {
        "title": "BB-ABCD1234",
        "price": 1000.0,
        "start_location_id": 60003760,
        "acceptor_id": 98000001,
    }
    defaults.update(overrides)
    return defaults


def _esi_items(type_id=34, quantity=1000):
    return [{"type_id": type_id, "quantity": quantity}]


class TestExtractTrackingNumber:
    def test_extracts_valid_number(self):
        assert extract_tracking_number("BB-ABCD1234 buyback") == "BB-ABCD1234"

    def test_case_insensitive(self):
        assert extract_tracking_number("bb-abcd1234") == "BB-ABCD1234"

    def test_returns_none_for_no_tracking_number(self):
        assert extract_tracking_number("just a random title") is None

    def test_returns_none_for_empty_title(self):
        assert extract_tracking_number("") is None


class TestMatchContract:
    def test_exact_match_no_flags(self):
        result = match_contract(_expectation(), _esi_contract(), _esi_items())
        assert result.status == "MATCHED"
        assert result.has_any_flag is False

    def test_wrong_item_type(self):
        result = match_contract(_expectation(), _esi_contract(), _esi_items(type_id=35))
        assert result.status == "FLAGGED"
        assert result.item_mismatch is True

    def test_wrong_quantity(self):
        result = match_contract(
            _expectation(), _esi_contract(), _esi_items(quantity=500)
        )
        assert result.status == "FLAGGED"
        assert result.item_mismatch is True

    def test_wrong_price_over(self):
        result = match_contract(
            _expectation(), _esi_contract(price=5000.0), _esi_items()
        )
        assert result.status == "FLAGGED"
        assert result.price_mismatch is True

    def test_wrong_price_under(self):
        result = match_contract(_expectation(), _esi_contract(price=10.0), _esi_items())
        assert result.status == "FLAGGED"
        assert result.price_mismatch is True

    def test_price_within_tolerance_not_flagged(self):
        result = match_contract(
            _expectation(), _esi_contract(price=1000.5), _esi_items()
        )
        assert result.price_mismatch is False

    def test_wrong_structure(self):
        result = match_contract(
            _expectation(), _esi_contract(start_location_id=99999999), _esi_items()
        )
        assert result.status == "FLAGGED"
        assert result.structure_mismatch is True

    def test_wrong_receiver(self):
        result = match_contract(
            _expectation(), _esi_contract(acceptor_id=90000001), _esi_items()
        )
        assert result.status == "FLAGGED"
        assert result.receiver_mismatch is True

    def test_title_tampered(self):
        result = match_contract(
            _expectation(), _esi_contract(title="BB-ZZZZ9999"), _esi_items()
        )
        assert result.status == "FLAGGED"
        assert result.title_tampered is True
        assert result.no_tracking is False

    def test_no_tracking_number_scam(self):
        result = match_contract(
            _expectation(), _esi_contract(title="just selling stuff"), _esi_items()
        )
        assert result.status == "FLAGGED"
        assert result.no_tracking is True
        assert result.title_tampered is False

    def test_multiple_simultaneous_mismatches(self):
        result = match_contract(
            _expectation(),
            _esi_contract(price=5000.0, start_location_id=1),
            _esi_items(type_id=99),
        )
        assert result.status == "FLAGGED"
        assert result.item_mismatch is True
        assert result.price_mismatch is True
        assert result.structure_mismatch is True

    def test_tracking_number_belongs_to_different_contract(self):
        """Cross-contamination: the title has a well-formed tracking number,
        but not the one this specific BuybackContract expects."""
        expectation = _expectation(tracking_number="BB-AAAA1111")
        result = match_contract(
            expectation, _esi_contract(title="BB-BBBB2222"), _esi_items()
        )
        assert result.title_tampered is True

    def test_multiple_item_types_matched_correctly(self):
        expectation = _expectation(
            expected_items=[
                ExpectedItem(type_id=34, quantity=1000),
                ExpectedItem(type_id=35, quantity=500),
            ]
        )
        items = [
            {"type_id": 34, "quantity": 1000},
            {"type_id": 35, "quantity": 500},
        ]
        result = match_contract(expectation, _esi_contract(), items)
        assert result.item_mismatch is False
