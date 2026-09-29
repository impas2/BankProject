from enum import Enum
from types import MappingProxyType

from account_errors import InvalidOperationError
from decimal import Decimal
from typing import Optional, Callable
from uuid import UUID

from currency import Currency
from models.abstract_account import AccountType, Person, AccountStatus
from models.bank_account import BankAccount


class InvestmentActive(Enum):
    BONDS = 0
    ETF = 1
    STOCKS = 2

class InvestmentAccount(BankAccount):
    def __init__(self, person: Person,
                 account_id: Optional[UUID], currency: Currency,
                 account_number: Optional[str] = None,
                 growth_rates: Optional[dict] = None,
                 ) -> None:

        super().__init__(person, account_id, currency, account_number,
                         AccountType.INVESTMENT)
        self._portfolio = {InvestmentActive.BONDS: Decimal(0), InvestmentActive.ETF: Decimal(0),
                           InvestmentActive.STOCKS: Decimal(0)}
        if growth_rates != None:
            for key in growth_rates:
                self.validate_rate(growth_rates[key])
            self.growth_rates = growth_rates
        else:
            self.growth_rates = {InvestmentActive.BONDS: Decimal(0), InvestmentActive.ETF: Decimal(0),
                                 InvestmentActive.STOCKS: Decimal(0)}

        self.account_status = AccountStatus.ACTIVE

    def validate_rate(self, rate: Decimal) -> None:
        if not isinstance(rate, Decimal):
            raise InvalidOperationError("Сумма должна быть Decimal")

        if not rate.is_finite():
            raise InvalidOperationError("Сумма должна быть конечным числом")

    def project_yearly_growth(
        self, growth_rates: dict[InvestmentActive, Decimal]
    ) -> Decimal:
        if not isinstance(growth_rates, dict):
            raise InvalidOperationError("Ставки должны быть переданы словарём")

        for asset, rate in growth_rates.items():
            if not isinstance(asset, InvestmentActive):
                raise InvalidOperationError("Неизвестный тип актива в ставках")

            if not isinstance(rate, Decimal) or not rate.is_finite():
                raise InvalidOperationError(
                    "Ставка должна быть конечным числом Decimal"
                )

        yearly_growth = Decimal(0)
        for asset, invested_amount in self._portfolio.items():
            if invested_amount == 0:
                continue

            if asset not in growth_rates:
                raise InvalidOperationError(
                    f"Не указана ставка для актива {asset.name}"
                )

            yearly_growth += invested_amount * growth_rates[asset]

        return yearly_growth

    @property
    def get_portfolio(self):
        return MappingProxyType(self._portfolio)

    @property
    def get_growth_rates(self):
        return self.growth_rates

    def invest(self, active_type: InvestmentActive, amount: Decimal) -> None:
        if not isinstance(active_type, InvestmentActive):
            raise InvalidOperationError("Тип актива должен быть указан из имеющихся")
        if not isinstance(amount, Decimal):
            raise InvalidOperationError("Сумма должен быть Decimal")
        if not amount.is_finite():
            raise InvalidOperationError("Должен быть конечным")

        if amount > 0:
            self.withdraw(amount, self.currency)
            self._portfolio[active_type] += amount
        else:
            raise InvalidOperationError()

    def get_portfolio_amount(self):
        portfolio_amt = Decimal(0)
        for key in self._portfolio:
            portfolio_amt += self._portfolio[key]
        return portfolio_amt

    def __str__(self):
        return (
            f"Account {self.account_id} has {self.type} {self.person} "
            f"{self.account_number[-4:]} {self.get_balance} "
            f"{self.currency} {self.account_status} {self.get_growth_rates} {self.get_portfolio}"
        )

    def get_account_info(self) -> None:
        print(
            f"Account {self.account_id} has {self.get_balance} {self.currency} {self.account_status} {self.get_growth_rates} {self.get_portfolio}")
