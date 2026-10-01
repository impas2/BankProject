from collections.abc import Callable
from decimal import Decimal
from typing import Any
from uuid import uuid4

import pytest

from models.account.currency import Currency
from models.account.abstract_account import Person
from models.account.investment_account import InvestmentAccount
from models.account.premium_account import PremiumAccount
from models.account.savings_account import SavingsAccount


def account_details() -> dict[str, Any]:
    """Каждый вызов создаёт новые реквизиты и владельца."""
    return {
        "person": Person("Ivanov", 30, "Moscow", "01.01.1996"),
        "account_id": uuid4(),
        "currency": Currency.USD,
        "account_number": "1234567890",
    }


@pytest.fixture
def account_creation_data() -> dict[str, Any]:
    """Общие аргументы конструктора без номера счёта."""
    details = account_details()
    del details["account_number"]
    return details


@pytest.fixture
def make_savings_account() -> Callable[..., SavingsAccount]:
    def make(
        *,
        balance: Decimal = Decimal("1000"),
        min_balance: Decimal = Decimal("300"),
        monthly_interest_rate: Decimal = Decimal("0.01"),
    ) -> SavingsAccount:
        account = SavingsAccount(
            **account_details(),
            min_balance=min_balance,
            monthly_interest_rate=monthly_interest_rate,
        )
        if balance != 0:
            account.deposit(balance, Currency.USD)
        return account

    return make


@pytest.fixture
def make_premium_account() -> Callable[..., PremiumAccount]:
    def make(
        *,
        balance: Decimal = Decimal("1000"),
        withdrawal_limit: Decimal = Decimal("2000"),
        overdraft_limit: Decimal = Decimal("500"),
        withdrawal_fee: Decimal = Decimal("50"),
    ) -> PremiumAccount:
        account = PremiumAccount(
            **account_details(),
            withdrawal_limit=withdrawal_limit,
            overdraft_limit=overdraft_limit,
            withdrawal_fee=withdrawal_fee,
        )
        if balance != 0:
            account.deposit(balance, Currency.USD)
        return account

    return make


@pytest.fixture
def make_investment_account() -> Callable[..., InvestmentAccount]:
    def make(*, balance: Decimal = Decimal("5000")) -> InvestmentAccount:
        account = InvestmentAccount(**account_details(), growth_rates=None)
        if balance != 0:
            account.deposit(balance, Currency.USD)
        return account

    return make


@pytest.fixture(
    params=[
        pytest.param(Decimal("-0.01"), id="negative"),
        pytest.param(Decimal("NaN"), id="nan"),
        pytest.param(Decimal("sNaN"), id="signaling-nan"),
        pytest.param(Decimal("Infinity"), id="infinity"),
        pytest.param(Decimal("-Infinity"), id="negative-infinity"),
        pytest.param("100", id="string"),
        pytest.param(100, id="integer"),
        pytest.param(100.0, id="float"),
        pytest.param(True, id="boolean"),
        pytest.param(None, id="none"),
    ]
)
def invalid_nonnegative_decimal(request: pytest.FixtureRequest) -> Any:
    return request.param
