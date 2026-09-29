from collections.abc import Callable
from decimal import Decimal
from typing import Any

import pytest

from account_errors import (
    AccountClosedError,
    AccountFrozenError,
    InsufficientFundsError,
    InvalidOperationError,
)
from currency import Currency
from models.abstract_account import AccountStatus, AccountType
from models.savings_account import SavingsAccount


@pytest.fixture
def account(make_savings_account: Callable[..., SavingsAccount]) -> SavingsAccount:
    return make_savings_account()


class TestSavingsAccount:
    def test_account_has_savings_type(self, account: SavingsAccount) -> None:
        assert account.get_account_type is AccountType.SAVINGS
        assert account.account_status is AccountStatus.ACTIVE

    @pytest.mark.parametrize("amount", [Decimal("100"), Decimal("700")])
    def test_withdraw_allows_balance_at_or_above_minimum(
        self, account: SavingsAccount, amount: Decimal
    ) -> None:
        account.withdraw(amount, Currency.USD)

        assert account.get_balance == Decimal("1000") - amount

    def test_withdraw_rejects_balance_below_minimum(
        self, account: SavingsAccount
    ) -> None:
        with pytest.raises(InsufficientFundsError):
            account.withdraw(Decimal("700.01"), Currency.USD)

        assert account.get_balance == Decimal("1000")

    def test_zero_minimum_allows_withdrawing_entire_balance(
        self,
        make_savings_account: Callable[..., SavingsAccount],
    ) -> None:
        account = make_savings_account(min_balance=Decimal("0"))

        account.withdraw(Decimal("1000"), Currency.USD)

        assert account.get_balance == Decimal("0")

    def test_withdraw_rejects_invalid_amount_without_changing_balance(
        self, account: SavingsAccount, invalid_nonnegative_decimal: Any
    ) -> None:
        with pytest.raises(InvalidOperationError):
            account.withdraw(invalid_nonnegative_decimal, Currency.USD)

        assert account.get_balance == Decimal("1000")

    def test_withdraw_rejects_wrong_currency(self, account: SavingsAccount) -> None:
        with pytest.raises(InvalidOperationError):
            account.withdraw(Decimal("100"), Currency.EUR)

        assert account.get_balance == Decimal("1000")

    @pytest.mark.parametrize(
        ("status", "error"),
        [
            (AccountStatus.FROZEN, AccountFrozenError),
            (AccountStatus.CLOSED, AccountClosedError),
        ],
    )
    @pytest.mark.parametrize("operation", ["withdraw", "apply_monthly_interest"])
    def test_inactive_account_rejects_operations(
        self,
        account: SavingsAccount,
        status: AccountStatus,
        error: type[Exception],
        operation: str,
    ) -> None:
        account.account_status = status

        with pytest.raises(error):
            if operation == "withdraw":
                account.withdraw(Decimal("100"), Currency.USD)
            else:
                account.apply_monthly_interest()

        assert account.get_balance == Decimal("1000")

    @pytest.mark.parametrize(
        ("rate", "expected_balance"),
        [
            (Decimal("0"), Decimal("1000")),
            (Decimal("0.01"), Decimal("1010")),
            (Decimal("0.0123456"), Decimal("1012.35")),
        ],
    )
    def test_monthly_interest_uses_rate_and_rounds_to_cents(
        self,
        make_savings_account: Callable[..., SavingsAccount],
        rate: Decimal,
        expected_balance: Decimal,
    ) -> None:
        account = make_savings_account(monthly_interest_rate=rate)

        account.apply_monthly_interest()

        assert account.get_balance == expected_balance

    def test_second_month_uses_updated_balance(self, account: SavingsAccount) -> None:
        account.apply_monthly_interest()
        account.apply_monthly_interest()

        assert account.get_balance == Decimal("1020.10")

    @pytest.mark.parametrize("field", ["min_balance", "monthly_interest_rate"])
    def test_constructor_rejects_invalid_parameters(
        self,
        make_savings_account: Callable[..., SavingsAccount],
        field: str,
        invalid_nonnegative_decimal: Any,
    ) -> None:
        with pytest.raises(InvalidOperationError):
            make_savings_account(**{field: invalid_nonnegative_decimal})

    def test_str_contains_account_details(self, account: SavingsAccount) -> None:
        text = str(account)

        for value in ("Ivanov", "7890", "1000", "USD", "ACTIVE", "300"):
            assert value in text

    def test_account_info_includes_balance_currency_and_minimum(
        self, account: SavingsAccount, capsys: pytest.CaptureFixture[str]
    ) -> None:
        account.get_account_info()

        text = capsys.readouterr().out
        for value in ("1000", "USD", "300"):
            assert value in text
