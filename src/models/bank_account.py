import uuid
from decimal import Decimal
from typing import Optional
from uuid import UUID

from account_errors import (
    AccountClosedError,
    AccountFrozenError,
    InsufficientFundsError,
    InvalidOperationError,
)
from currency import Currency
from models.abstract_account import AbstractAccount, AccountStatus, AccountType, Person


class BankAccount(AbstractAccount):
    def __init__(
        self,
        person: Person,
        account_id: Optional[UUID],
        currency: Currency,
        account_number: Optional[str] = None,
        account_type: AccountType = AccountType.CURRENT,
        balance: Decimal = Decimal(0),
    ) -> None:
        if not isinstance(currency, Currency):
            raise InvalidOperationError("Валюта счёта должна быть Currency")

        if account_number is None:
            account_number = uuid.uuid4().hex[:12]
        if account_id is None:
            account_id = uuid.uuid4()
        super().__init__(person, account_id, account_number, account_type, balance)
        self.currency = currency

    def validate_frozen(self) -> None:
        if self.account_status == AccountStatus.FROZEN:
            raise AccountFrozenError(f"Account {self.account_id} is frozen")

    def validate_closed(self) -> None:
        if self.account_status == AccountStatus.CLOSED:
            raise AccountClosedError(f"Account {self.account_id} is closed")

    def validate_currency(self, currency: Currency) -> None:
        if self.currency != currency:
            raise InvalidOperationError(
                f"Account {self.account_id} does not support currency {currency}"
            )

    def validate_balance(self, amount: Decimal) -> None:
        if self.get_balance < amount:
            raise InsufficientFundsError(
                f"Account {self.account_id} does not have enough funds"
            )

    def validate_amount(self, amount: Decimal) -> None:
        if not isinstance(amount, Decimal):
            raise InvalidOperationError("Сумма должна быть Decimal")

        if not amount.is_finite():
            raise InvalidOperationError("Сумма должна быть конечным числом")

        if amount < 0:
            raise InvalidOperationError("Сумма не может быть отрицательной")

    def deposit(self, amount: Decimal, currency: Currency) -> None:
        self.validate_closed()
        self.validate_frozen()
        self.validate_currency(currency)
        self.validate_amount(amount)
        self._balance += amount

    def withdraw(self, amount: Decimal, currency: Currency) -> None:
        self.validate_closed()
        self.validate_frozen()
        self.validate_currency(currency)
        self.validate_amount(amount)
        self.validate_balance(amount)
        self._balance -= amount

    def get_account_info(self) -> None:
        print(f"Account {self.account_id} has {self.get_balance} {self.currency}")

    def __str__(self) -> str:
        return (
            f"Account {self.account_id} has {self.type} {self.person} "
            f"{self.account_number[-4:]} {self.get_balance} "
            f"{self.currency} {self.account_status}"
        )
