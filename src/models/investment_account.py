from enum import Enum

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
                 account_number: Optional[str],
                 growth_rates: Optional[dict]
                 ) -> None:

        super().__init__(person, account_id, currency, account_number,
                         AccountType.INVESTMENT)
        self._portfolio = {InvestmentActive.BONDS: 0, InvestmentActive.ETF: 0,
                           InvestmentActive.STOCKS: 0}
        if growth_rates != None:
            self.growth_rates = growth_rates
        else:
            self.growth_rates = {InvestmentActive.BONDS: 0, InvestmentActive.ETF: 0,
                                 InvestmentActive.STOCKS: 0}

        self.account_status = AccountStatus.ACTIVE

    def project_yearly_growth(self):
        yearly_growth = Decimal(0)
        for key, value in self._portfolio:
            yearly_growth += self.growth_rates[key] * value - value

        return yearly_growth

    @property
    def get_portfolio(self):
        return self._portfolio

    @property
    def get_growth_rates(self):
        return self.growth_rates

    def validate_amount(self, amount: Decimal) -> None:
        if not isinstance(amount, Decimal):
            raise InvalidOperationError("Сумма должна быть Decimal")

        if not amount.is_finite():
            raise InvalidOperationError("Сумма должна быть конечным числом")

        if amount <= 0:
            raise InvalidOperationError(
                "Сумма не может быть отрицательной или равной 0")

    def invest(self, active_type: InvestmentActive, amount: Decimal) -> None:
        if not isinstance(active_type, InvestmentActive):
            raise InvalidOperationError("Тип актива должен быть указан из имеющихся")
        if not isinstance(amount, Decimal):
            raise InvalidOperationError("Сумма должен быть Decimal")

        self.withdraw(amount, self.currency)
        self._portfolio[active_type] += amount

    

    def get_portfolio_amount(self):
        portfolio_amt = Decimal(0)
        for key, value in self._portfolio:
            portfolio_amt += value
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
