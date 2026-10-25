"""
Pure contract-matching / abuse-detection logic for the Buyback Program.

Deliberately has no DB access and no ESI calls, so it is fully unit-testable
with plain dataclasses and dicts - this is the single most valuable piece of
logic ported from the source third-party plugin (its best-tested part), kept
pure so `tasks/buyback.py` stays a thin fetch-and-write layer around it.
"""

# Standard Library
import re
from dataclasses import dataclass

# "<PREFIX>-<8 chars>", where each program picks its own 1-10 character prefix.
TRACKING_NUMBER_RE = re.compile(r"\b([A-Z0-9]{1,10})-[A-Z0-9]{8}\b")

# Tolerance for price mismatches, to absorb rounding differences between the
# quoted appraisal and what a member actually typed into the in-game contract.
PRICE_TOLERANCE = 1.0  # ISK


@dataclass
class ExpectedItem:
    type_id: int
    quantity: int


@dataclass
class BuybackContractExpectation:
    """What a BuybackContract + its items say should be in the real ESI contract."""

    tracking_number: str
    expected_items: list[ExpectedItem]
    expected_price: float
    # Any of these drop-off locations is fine; empty means don't check.
    expected_location_ids: set[int]
    expected_receiver_id: int | None = None


@dataclass
class ContractMatchResult:
    status: str  # one of BuybackContract.STATUS_CHOICES
    item_mismatch: bool = False
    price_mismatch: bool = False
    structure_mismatch: bool = False
    receiver_mismatch: bool = False
    title_tampered: bool = False
    no_tracking: bool = False
    # Asked less than quoted: noted, but not a reason for review - the seller
    # only shortchanges themselves.
    price_low: bool = False
    notes: str = ""

    @property
    def has_any_flag(self) -> bool:
        return any(
            [
                self.item_mismatch,
                self.price_mismatch,
                self.structure_mismatch,
                self.receiver_mismatch,
                self.title_tampered,
                self.no_tracking,
            ]
        )


def extract_tracking_number(contract_title: str, prefixes=None) -> str | None:
    """Extracts a <PREFIX>-XXXXXXXX tracking number from a contract title, or
    None if there is none (a likely scam/untracked contract, flagged
    separately from a tampered one). With `prefixes`, only tracking numbers
    using one of those prefixes count, so ordinary words with a dash in the
    title aren't mistaken for one."""
    if not contract_title:
        return None
    for match in TRACKING_NUMBER_RE.finditer(contract_title.upper()):
        if prefixes is None or match.group(1) in prefixes:
            return match.group(0)
    return None


def match_contract(
    expected: BuybackContractExpectation,
    esi_contract: dict,
    esi_contract_items: list[dict],
) -> ContractMatchResult:
    """
    Compares what a BuybackContract expects against the real ESI contract and
    its items, and returns the flags/status that should be written back.
    """
    notes: list[str] = []

    expected_prefix = expected.tracking_number.upper().rsplit("-", 1)[0]
    found_tracking = extract_tracking_number(
        esi_contract.get("title", ""), prefixes={expected_prefix}
    )
    no_tracking = found_tracking is None
    title_tampered = (
        not no_tracking and found_tracking != expected.tracking_number.upper()
    )
    if no_tracking:
        notes.append("Contract title has no recognizable tracking number.")
    elif title_tampered:
        notes.append(
            f"Tracking number in title ({found_tracking}) does not match the "
            f"expected one ({expected.tracking_number})."
        )

    structure_mismatch = bool(expected.expected_location_ids) and (
        esi_contract.get("start_location_id") not in expected.expected_location_ids
    )
    if structure_mismatch:
        notes.append("Contract was created at the wrong structure/location.")

    # acceptor_id is only set once the contract has actually been accepted;
    # assignee_id is the intended recipient on a directed contract before
    # that. Whichever of the two is actually present on this contract is the
    # one checked - an absent field is unknown, not treated as a match.
    actual_receiver_id = esi_contract.get("acceptor_id") or esi_contract.get(
        "assignee_id"
    )
    receiver_mismatch = (
        expected.expected_receiver_id is not None
        and actual_receiver_id is not None
        and actual_receiver_id != expected.expected_receiver_id
    )
    if receiver_mismatch:
        notes.append(
            "Contract was not issued to the expected receiving corp/character."
        )

    price_diff = float(esi_contract.get("price", 0.0)) - expected.expected_price
    price_mismatch = price_diff > PRICE_TOLERANCE
    price_low = price_diff < -PRICE_TOLERANCE
    if price_mismatch:
        notes.append(
            f"Contract asks {esi_contract.get('price', 0.0):,.2f} ISK, more than "
            f"the quoted {expected.expected_price:,.2f} ISK."
        )
    elif price_low:
        notes.append(
            f"Contract asks {esi_contract.get('price', 0.0):,.2f} ISK, less than "
            f"the quoted {expected.expected_price:,.2f} ISK; the seller receives less."
        )

    item_mismatch = _items_mismatch(expected.expected_items, esi_contract_items)
    if item_mismatch:
        notes.append("Contract items do not match what was quoted.")

    result = ContractMatchResult(
        status="MATCHED",
        item_mismatch=item_mismatch,
        price_mismatch=price_mismatch,
        structure_mismatch=structure_mismatch,
        receiver_mismatch=receiver_mismatch,
        title_tampered=title_tampered,
        no_tracking=no_tracking,
        price_low=price_low,
        notes=" ".join(notes),
    )
    if result.has_any_flag:
        result.status = "FLAGGED"

    return result


def _items_mismatch(expected_items: list[ExpectedItem], esi_items: list[dict]) -> bool:
    expected_by_type: dict[int, int] = {}
    for item in expected_items:
        expected_by_type[item.type_id] = (
            expected_by_type.get(item.type_id, 0) + item.quantity
        )

    actual_by_type: dict[int, int] = {}
    for item in esi_items:
        type_id = item.get("type_id")
        quantity = item.get("quantity", 0)
        actual_by_type[type_id] = actual_by_type.get(type_id, 0) + quantity

    return expected_by_type != actual_by_type
