from decimal import Decimal
from typing import Optional
from uuid import UUID

from account_errors import InvalidOperationError, InsufficientFundsError
from currency import Currency
from models.abstract_account import AccountType, Person, AccountStatus
from models.bank_account import BankAccount


class PremiumAccount(BankAccount):
    def __init__(self, person: Person,
                 account_id: Optional[UUID], currency: Currency,
                 account_number: Optional[str] = None,
                 withdrawal_limit: Decimal = Decimal(0),
                 overdraft_limit: Decimal = Decimal(0),
                 withdrawal_fee: Decimal = Decimal(0),
                 ) -> None:

        super().__init__(person, account_id, currency, account_number, AccountType.CURRENT)

        if not isinstance(withdrawal_limit, Decimal):
            raise InvalidOperationError("Лимит вывода должен быть Decimal")
        if not isinstance(overdraft_limit, Decimal):
            raise InvalidOperationError("Овердрафт должна быть Decimal")
        if not isinstance(withdrawal_fee, Decimal):
            raise InvalidOperationError("Комиссия должна быть Decimal")

        self.account_status = AccountStatus.ACTIVE
        self.validate_amount(withdrawal_limit)
        self.validate_amount(overdraft_limit)
        self.validate_amount(withdrawal_fee)

        self.withdrawal_limit = withdrawal_limit
        self.overdraft_limit = overdraft_limit
        self.withdrawal_fee = withdrawal_fee

    def withdraw(self, amount: Decimal, currency: Currency) -> None:
        self.validate_closed()
        self.validate_frozen()
        self.validate_currency(currency)
        self.validate_amount(amount)

        if amount > self.withdrawal_limit :
            raise InvalidOperationError(
                f"Account {self.account_id} unable to make operation"
            )
        if self.get_balance + self.overdraft_limit - amount - self.withdrawal_fee < 0 :
            raise InsufficientFundsError(
                f"Account {self.account_id} unable to make operation"
            )
        self._balance = self._balance - amount - self.withdrawal_fee

    def __str__(self):
        return (
            f"Account {self.account_id} has {self.type} {self.person} "
            f"{self.account_number[-4:]} {self.get_balance} "
            f"{self.currency} {self.account_status} {self.withdrawal_limit} {self.overdraft_limit} {self.withdrawal_fee}"
        )
    def get_account_info(self) -> None:
        print(f"Account {self.account_id} has {self.get_balance} {self.currency} {self.account_status} {self.withdrawal_limit} {self.overdraft_limit} {self.withdrawal_fee}")
