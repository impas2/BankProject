import re
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
from models.premium_account import PremiumAccount


@pytest.fixture
def account(make_premium_account: Callable[..., PremiumAccount]) -> PremiumAccount:
    return make_premium_account()


class TestPremiumAccount:
    @pytest.mark.parametrize("number_kwargs", [{}, {"account_number": None}])
    def test_accepts_omitted_or_none_account_number(
        self,
        account_creation_data: dict[str, Any],
        number_kwargs: dict[str, Any],
    ) -> None:
        account = PremiumAccount(**account_creation_data, **number_kwargs)

        assert re.fullmatch(r"[0-9a-f]{12}", account.account_number)
        assert account.account_id == account_creation_data["account_id"]
        assert account.get_account_type is AccountType.CURRENT

    @pytest.mark.parametrize(
        ("amount", "expected_balance"),
        [
            (Decimal("100"), Decimal("850")),
            (Decimal("1000"), Decimal("-50")),
            (Decimal("1450"), Decimal("-500")),
        ],
    )
    def test_withdraw_charges_fee_once_and_allows_overdraft(
        self, account: PremiumAccount, amount: Decimal, expected_balance: Decimal
    ) -> None:
        account.withdraw(amount, Currency.USD)

        assert account.get_balance == expected_balance

    def test_withdraw_rejects_overdraft_overrun_including_fee(
        self,
        account: PremiumAccount,
    ) -> None:
        with pytest.raises(InsufficientFundsError):
            account.withdraw(Decimal("1450.01"), Currency.USD)

        assert account.get_balance == Decimal("1000")

    def test_withdraw_rejects_operation_limit_even_with_enough_money(
        self,
        make_premium_account: Callable[..., PremiumAccount],
    ) -> None:
        account = make_premium_account(balance=Decimal("10000"))

        with pytest.raises(InvalidOperationError):
            account.withdraw(Decimal("2000.01"), Currency.USD)

        assert account.get_balance == Decimal("10000")

    def test_operation_limit_applies_to_requested_amount_before_fee(
        self,
        make_premium_account: Callable[..., PremiumAccount],
    ) -> None:
        account = make_premium_account(balance=Decimal("5000"))

        account.withdraw(Decimal("2000"), Currency.USD)

        assert account.get_balance == Decimal("2950")

    def test_zero_operation_limit_forbids_withdrawal(
        self,
        make_premium_account: Callable[..., PremiumAccount],
    ) -> None:
        account = make_premium_account(withdrawal_limit=Decimal("0"))

        with pytest.raises(InvalidOperationError):
            account.withdraw(Decimal("1"), Currency.USD)

        assert account.get_balance == Decimal("1000")

    def test_zero_overdraft_forbids_negative_balance(
        self,
        make_premium_account: Callable[..., PremiumAccount],
    ) -> None:
        account = make_premium_account(overdraft_limit=Decimal("0"))

        with pytest.raises(InsufficientFundsError):
            account.withdraw(Decimal("951"), Currency.USD)

        assert account.get_balance == Decimal("1000")

    def test_zero_fee_is_allowed(
        self,
        make_premium_account: Callable[..., PremiumAccount],
    ) -> None:
        account = make_premium_account(withdrawal_fee=Decimal("0"))

        account.withdraw(Decimal("100"), Currency.USD)

        assert account.get_balance == Decimal("900")

    def test_deposit_repays_overdraft_without_withdrawal_fee(
        self,
        account: PremiumAccount,
    ) -> None:
        account.withdraw(Decimal("1450"), Currency.USD)

        account.deposit(Decimal("600"), Currency.USD)

        assert account.get_balance == Decimal("100")

    def test_withdraw_rejects_invalid_amount_without_charging_fee(
        self, account: PremiumAccount, invalid_nonnegative_decimal: Any
    ) -> None:
        with pytest.raises(InvalidOperationError):
            account.withdraw(invalid_nonnegative_decimal, Currency.USD)

        assert account.get_balance == Decimal("1000")

    def test_withdraw_rejects_wrong_currency_without_charging_fee(
        self,
        account: PremiumAccount,
    ) -> None:
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
    def test_inactive_account_rejects_withdrawal_without_charging_fee(
        self, account: PremiumAccount, status: AccountStatus, error: type[Exception]
    ) -> None:
        account.account_status = status

        with pytest.raises(error):
            account.withdraw(Decimal("100"), Currency.USD)

        assert account.get_balance == Decimal("1000")

    @pytest.mark.parametrize(
        "field", ["withdrawal_limit", "overdraft_limit", "withdrawal_fee"]
    )
    def test_constructor_rejects_invalid_parameters(
        self,
        make_premium_account: Callable[..., PremiumAccount],
        field: str,
        invalid_nonnegative_decimal: Any,
    ) -> None:
        with pytest.raises(InvalidOperationError):
            make_premium_account(**{field: invalid_nonnegative_decimal})

    def test_str_contains_account_details_and_limits(
        self, account: PremiumAccount
    ) -> None:
        text = str(account)

        for value in ("Ivanov", "7890", "1000", "USD", "ACTIVE", "2000", "500", "50"):
            assert value in text

    def test_account_info_includes_balance_currency_and_limits(
        self, account: PremiumAccount, capsys: pytest.CaptureFixture[str]
    ) -> None:
        account.get_account_info()

        text = capsys.readouterr().out
        for value in ("1000", "USD", "2000", "500", "50"):
            assert value in text
