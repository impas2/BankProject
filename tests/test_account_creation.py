from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

import pytest

from account_errors import InvalidOperationError
from currency import Currency
from models.abstract_account import AccountStatus, AccountType, Person
from models.bank_account import BankAccount


@pytest.fixture
def account_data() -> dict[str, Any]:
    return {
        "person": Person("Ivanov", 28, "somewhere", "01.01.2022"),
        "account_id": uuid4(),
        "currency": Currency.USD,
        "account_number": "001234567890",
        "account_type": AccountType.CURRENT,
        "balance": Decimal("100.50"),
    }


@pytest.mark.parametrize(
    ("field", "value"),
    [
        pytest.param("balance", Decimal("-0.01"), id="negative-balance"),
        pytest.param("balance", Decimal("Infinity"), id="infinite-balance"),
        pytest.param("balance", Decimal("-Infinity"), id="negative-infinity"),
        pytest.param("balance", Decimal("NaN"), id="nan-balance"),
        pytest.param("balance", Decimal("sNaN"), id="signaling-nan-balance"),
        pytest.param("balance", 0, id="integer-balance"),
        pytest.param("balance", 100.5, id="float-balance"),
        pytest.param("balance", "100.50", id="string-balance"),
        pytest.param("balance", None, id="missing-balance"),
        pytest.param("balance", True, id="true-balance"),
        pytest.param("balance", False, id="false-balance"),
        pytest.param("currency", "BTC", id="unsupported-currency"),
        pytest.param("currency", "USD", id="string-currency"),
        pytest.param("currency", 1, id="integer-currency"),
        pytest.param("currency", True, id="boolean-currency"),
        pytest.param("currency", None, id="missing-currency"),
        pytest.param("account_id", "not-a-uuid", id="invalid-uuid-string"),
        pytest.param(
            "account_id",
            "550e8400-e29b-41d4-a716-446655440000",
            id="valid-uuid-as-string",
        ),
        pytest.param("account_id", 123, id="integer-uuid"),
        pytest.param("account_id", True, id="boolean-uuid"),
        pytest.param("account_number", "", id="empty-number"),
        pytest.param("account_number", "   ", id="blank-number"),
        pytest.param("account_number", "\t\n", id="whitespace-number"),
        pytest.param("account_number", 1234567890, id="integer-number"),
        pytest.param("account_number", True, id="boolean-number"),
        pytest.param("person", None, id="missing-owner"),
        pytest.param("person", "Ivanov", id="string-owner"),
        pytest.param("account_type", None, id="missing-account-type"),
        pytest.param("account_type", "CURRENT", id="string-account-type"),
        pytest.param("account_type", 0, id="integer-account-type"),
    ],
)
def test_constructor_rejects_invalid_data(
    account_data: dict[str, Any], field: str, value: Any
) -> None:
    account_data[field] = value

    with pytest.raises(InvalidOperationError):
        BankAccount(**account_data)


@pytest.mark.parametrize("currency", list(Currency))
@pytest.mark.parametrize("balance", [Decimal("0"), Decimal("100.50")])
def test_constructor_preserves_valid_data(
    account_data: dict[str, Any], currency: Currency, balance: Decimal
) -> None:
    account_data.update(currency=currency, balance=balance)

    account = BankAccount(**account_data)

    assert account.get_balance == balance
    assert account.currency is currency
    assert account.account_id == account_data["account_id"]
    assert account.account_number == "001234567890"
    assert account.person is account_data["person"]
    assert account.get_account_type is AccountType.CURRENT
    assert account.account_status is AccountStatus.ACTIVE


def test_constructor_defaults_to_zero_balance(account_data: dict[str, Any]) -> None:
    del account_data["balance"]

    account = BankAccount(**account_data)

    assert account.get_balance == Decimal("0")


@pytest.mark.parametrize(
    "missing_fields",
    [("account_id",), ("account_number",), ("account_id", "account_number")],
)
def test_constructor_generates_missing_identifiers(
    account_data: dict[str, Any], missing_fields: tuple[str, ...]
) -> None:
    for field in missing_fields:
        account_data[field] = None

    first_account = BankAccount(**account_data)
    second_account = BankAccount(**account_data)

    assert isinstance(first_account.account_id, UUID)
    assert isinstance(first_account.account_number, str)
    assert first_account.account_number.strip()
    for field in ("account_id", "account_number"):
        if field in missing_fields:
            assert getattr(first_account, field) != getattr(second_account, field)
        else:
            assert getattr(first_account, field) == account_data[field]


@pytest.mark.parametrize(
    ("field", "value"),
    [("balance", Decimal("-1")), ("currency", "BTC")],
)
def test_constructor_validates_before_storing_fields(
    account_data: dict[str, Any], field: str, value: Any
) -> None:
    account_data[field] = value
    account = BankAccount.__new__(BankAccount)

    with pytest.raises(InvalidOperationError):
        account.__init__(**account_data)

    assert vars(account) == {}
