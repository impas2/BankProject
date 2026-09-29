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
from models.investment_account import InvestmentAccount, InvestmentActive


@pytest.fixture
def account(
    make_investment_account: Callable[..., InvestmentAccount],
) -> InvestmentAccount:
    return make_investment_account()


@pytest.fixture
def growth_rates() -> dict[InvestmentActive, Decimal]:
    return {
        InvestmentActive.STOCKS: Decimal("0.10"),
        InvestmentActive.BONDS: Decimal("0.04"),
        InvestmentActive.ETF: Decimal("0.07"),
    }


@pytest.fixture
def invested_account(account: InvestmentAccount) -> InvestmentAccount:
    account.invest(InvestmentActive.STOCKS, Decimal("1000"))
    account.invest(InvestmentActive.BONDS, Decimal("2000"))
    account.invest(InvestmentActive.ETF, Decimal("1000"))
    return account


class TestInvestmentAccount:
    @pytest.mark.parametrize("number_kwargs", [{}, {"account_number": None}])
    def test_accepts_omitted_or_none_account_number(
        self,
        account_creation_data: dict[str, Any],
        number_kwargs: dict[str, Any],
    ) -> None:
        account = InvestmentAccount(**account_creation_data, **number_kwargs)

        assert re.fullmatch(r"[0-9a-f]{12}", account.account_number)
        assert account.account_id == account_creation_data["account_id"]
        assert account.get_account_type is AccountType.INVESTMENT

    def test_account_starts_with_empty_investments(
        self, account: InvestmentAccount
    ) -> None:
        assert account.get_account_type is AccountType.INVESTMENT
        assert sum(account.get_portfolio.values()) == Decimal("0")
        assert account.get_portfolio_amount() == Decimal("0")
        assert account.get_balance == Decimal("5000")

    @pytest.mark.parametrize("asset", list(InvestmentActive))
    def test_invest_moves_money_from_cash_to_selected_asset(
        self, account: InvestmentAccount, asset: InvestmentActive
    ) -> None:
        account.invest(asset, Decimal("300"))

        assert account.get_balance == Decimal("4700")
        assert account.get_portfolio[asset] == Decimal("300")
        assert sum(account.get_portfolio.values()) == Decimal("300")

    def test_repeated_investment_accumulates_amount(
        self, account: InvestmentAccount
    ) -> None:
        account.invest(InvestmentActive.STOCKS, Decimal("300"))
        account.invest(InvestmentActive.STOCKS, Decimal("200"))

        assert account.get_portfolio[InvestmentActive.STOCKS] == Decimal("500")
        assert account.get_balance == Decimal("4500")

    def test_invest_all_available_cash(self, account: InvestmentAccount) -> None:
        account.invest(InvestmentActive.ETF, Decimal("5000"))

        assert account.get_balance == Decimal("0")
        assert account.get_portfolio[InvestmentActive.ETF] == Decimal("5000")

    @pytest.mark.parametrize("asset", ["crypto", None, 123])
    def test_invest_rejects_unknown_asset_without_changing_state(
        self, account: InvestmentAccount, asset: Any
    ) -> None:
        portfolio_before = dict(account.get_portfolio)

        with pytest.raises(InvalidOperationError):
            account.invest(asset, Decimal("100"))

        assert account.get_balance == Decimal("5000")
        assert account.get_portfolio == portfolio_before

    def test_invest_rejects_invalid_amount_without_changing_state(
        self, account: InvestmentAccount, invalid_nonnegative_decimal: Any
    ) -> None:
        portfolio_before = dict(account.get_portfolio)

        with pytest.raises(InvalidOperationError):
            account.invest(InvestmentActive.STOCKS, invalid_nonnegative_decimal)

        assert account.get_balance == Decimal("5000")
        assert account.get_portfolio == portfolio_before

    def test_invest_rejects_zero(self, account: InvestmentAccount) -> None:
        portfolio_before = dict(account.get_portfolio)

        with pytest.raises(InvalidOperationError):
            account.invest(InvestmentActive.STOCKS, Decimal("0"))

        assert account.get_balance == Decimal("5000")
        assert account.get_portfolio == portfolio_before

    @pytest.mark.parametrize("operation", ["invest", "withdraw"])
    def test_invested_money_is_not_available_as_cash(
        self, invested_account: InvestmentAccount, operation: str
    ) -> None:
        portfolio_before = dict(invested_account.get_portfolio)

        with pytest.raises(InsufficientFundsError):
            if operation == "invest":
                invested_account.invest(InvestmentActive.STOCKS, Decimal("1000.01"))
            else:
                invested_account.withdraw(Decimal("1000.01"), Currency.USD)

        assert invested_account.get_balance == Decimal("1000")
        assert invested_account.get_portfolio == portfolio_before

    @pytest.mark.parametrize(
        ("status", "error"),
        [
            (AccountStatus.FROZEN, AccountFrozenError),
            (AccountStatus.CLOSED, AccountClosedError),
        ],
    )
    def test_inactive_account_rejects_investing_without_changing_state(
        self,
        account: InvestmentAccount,
        status: AccountStatus,
        error: type[Exception],
    ) -> None:
        portfolio_before = dict(account.get_portfolio)
        account.account_status = status

        with pytest.raises(error):
            account.invest(InvestmentActive.STOCKS, Decimal("100"))

        assert account.get_balance == Decimal("5000")
        assert account.get_portfolio == portfolio_before

    def test_portfolio_total_excludes_free_cash(
        self, invested_account: InvestmentAccount
    ) -> None:
        assert invested_account.get_portfolio_amount() == Decimal("4000")
        assert invested_account.get_balance == Decimal("1000")

    def test_yearly_projection_returns_growth_and_preserves_state(
        self,
        invested_account: InvestmentAccount,
        growth_rates: dict[InvestmentActive, Decimal],
    ) -> None:
        portfolio_before = dict(invested_account.get_portfolio)
        rates_before = dict(growth_rates)

        first_result = invested_account.project_yearly_growth(growth_rates)
        second_result = invested_account.project_yearly_growth(growth_rates)

        assert isinstance(first_result, Decimal)
        assert first_result == second_result == Decimal("250")
        assert invested_account.get_balance == Decimal("1000")
        assert invested_account.get_portfolio == portfolio_before
        assert growth_rates == rates_before

    def test_projection_uses_rates_from_each_call(
        self,
        invested_account: InvestmentAccount,
        growth_rates: dict[InvestmentActive, Decimal],
    ) -> None:
        zero_rates = dict.fromkeys(InvestmentActive, Decimal("0"))

        assert invested_account.project_yearly_growth(growth_rates) == Decimal("250")
        assert invested_account.project_yearly_growth(zero_rates) == Decimal("0")

    def test_projection_of_empty_portfolio_is_zero(
        self, account: InvestmentAccount
    ) -> None:
        result = account.project_yearly_growth({})

        assert isinstance(result, Decimal)
        assert result == Decimal("0")
        assert account.get_balance == Decimal("5000")

    @pytest.mark.parametrize("rate", [Decimal("0.10"), Decimal("-0.10")])
    def test_projection_requires_rates_only_for_invested_assets(
        self, account: InvestmentAccount, rate: Decimal
    ) -> None:
        account.invest(InvestmentActive.STOCKS, Decimal("1000"))

        result = account.project_yearly_growth({InvestmentActive.STOCKS: rate})

        assert result == Decimal("1000") * rate
        assert account.get_balance == Decimal("4000")

    @pytest.mark.parametrize(
        "rates",
        [
            None,
            [],
            "stocks",
            {},
            {"crypto": Decimal("0.1")},
            pytest.param(
                {InvestmentActive.STOCKS: Decimal("0.1")},
                id="missing-bonds-and-etf",
            ),
        ],
    )
    def test_projection_rejects_invalid_or_incomplete_rates(
        self, invested_account: InvestmentAccount, rates: Any
    ) -> None:
        portfolio_before = dict(invested_account.get_portfolio)

        with pytest.raises(InvalidOperationError):
            invested_account.project_yearly_growth(rates)

        assert invested_account.get_balance == Decimal("1000")
        assert invested_account.get_portfolio == portfolio_before

    def test_projection_rejects_unknown_asset_even_if_required_rates_are_present(
        self,
        invested_account: InvestmentAccount,
        growth_rates: dict[InvestmentActive, Decimal],
    ) -> None:
        rates = {**growth_rates, "crypto": Decimal("0.1")}
        portfolio_before = dict(invested_account.get_portfolio)

        with pytest.raises(InvalidOperationError):
            invested_account.project_yearly_growth(rates)

        assert invested_account.get_balance == Decimal("1000")
        assert invested_account.get_portfolio == portfolio_before

    @pytest.mark.parametrize(
        "rate",
        [
            Decimal("NaN"),
            Decimal("sNaN"),
            Decimal("Infinity"),
            Decimal("-Infinity"),
            "0.1",
            0.1,
            1,
            True,
            None,
        ],
    )
    def test_projection_rejects_invalid_rate_values(
        self,
        invested_account: InvestmentAccount,
        growth_rates: dict[InvestmentActive, Decimal],
        rate: Any,
    ) -> None:
        growth_rates[InvestmentActive.STOCKS] = rate
        portfolio_before = dict(invested_account.get_portfolio)

        with pytest.raises(InvalidOperationError):
            invested_account.project_yearly_growth(growth_rates)

        assert invested_account.get_balance == Decimal("1000")
        assert invested_account.get_portfolio == portfolio_before

    @pytest.mark.parametrize("asset", [InvestmentActive.STOCKS, "crypto"])
    def test_portfolio_view_cannot_change_account_state(
        self, invested_account: InvestmentAccount, asset: Any
    ) -> None:
        portfolio_before = dict(invested_account.get_portfolio)
        portfolio_view = invested_account.get_portfolio

        try:
            portfolio_view[asset] = Decimal("9999")
        except TypeError:
            pass  # Неизменяемое представление тоже удовлетворяет контракту.

        assert invested_account.get_portfolio == portfolio_before
        assert invested_account.get_balance == Decimal("1000")

    def test_different_accounts_do_not_share_portfolio(
        self, make_investment_account: Callable[..., InvestmentAccount]
    ) -> None:
        first_account = make_investment_account()
        second_account = make_investment_account()

        first_account.invest(InvestmentActive.STOCKS, Decimal("300"))

        assert sum(second_account.get_portfolio.values()) == Decimal("0")
        assert second_account.get_balance == Decimal("5000")

    def test_str_contains_account_details(self, account: InvestmentAccount) -> None:
        text = str(account)

        for value in ("Ivanov", "7890", "5000", "USD", "ACTIVE"):
            assert value in text

    def test_account_info_includes_free_balance_and_currency(
        self, account: InvestmentAccount, capsys: pytest.CaptureFixture[str]
    ) -> None:
        account.get_account_info()

        text = capsys.readouterr().out
        assert "5000" in text
        assert "USD" in text
