from decimal import Decimal
from typing import Optional
from uuid import UUID

from models.account.account_errors import InvalidOperationError, InsufficientFundsError
from models.account.currency import Currency
from models.account.abstract_account import Person, AccountType, AccountStatus
from models.account.bank_account import BankAccount

class SavingsAccount(BankAccount):
    def __init__(self, person: Person,
                 account_id: Optional[UUID], currency: Currency,
                 account_number: Optional[str] = None,
                 min_balance: Decimal = Decimal(0),
                 monthly_interest_rate: Decimal = Decimal(0)) -> None:

        super().__init__(person, account_id, currency, account_number, AccountType.SAVINGS)

        if not isinstance(min_balance, Decimal):
            raise InvalidOperationError("Баланс должен быть Decimal")
        if not isinstance(monthly_interest_rate, Decimal):
            raise InvalidOperationError("Ставка должна быть Decimal")

        self.validate_amount(min_balance)
        self.min_balance = min_balance
        self.account_status = AccountStatus.ACTIVE
        self.validate_amount(monthly_interest_rate)
        self.monthly_interest_rate = monthly_interest_rate

    def withdraw(self, amount: Decimal, currency: Currency) -> None:
        self.validate_closed()
        self.validate_frozen()
        self.validate_currency(currency)
        self.validate_amount(amount)

        if self.get_balance - amount < self.min_balance:
            raise InsufficientFundsError(
                f"Account {self.account_id} unable to make operation"
            )
        self._balance -= amount

    def __str__(self):
        return (
            f"Account {self.account_id} has {self.type} {self.person} "
            f"{self.account_number[-4:]} {self.get_balance} "
            f"{self.currency} {self.account_status} {self.monthly_interest_rate} {self.min_balance}"
        )
    def get_account_info(self) -> None:
        print(f"Account {self.account_id} has {self.get_balance} {self.currency} {self.account_status} {self.monthly_interest_rate} {self.min_balance}")

    def apply_monthly_interest(self) -> None:
        interest = (self.get_balance * self.monthly_interest_rate).quantize(Decimal("0.01"))
        self.deposit(interest, self.currency)
