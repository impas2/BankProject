from json.decoder import NaN

from models.abstract_account import Person
from uuid import UUID as uuid
from models.abstract_account import AbstractAccount
from currency import Currency
from models.abstract_account import AccountStatus
from account_errors import AccountClosedError, InvalidOperationError, InsufficientFundsError
from account_errors import AccountFrozenError
from decimal import Decimal

class BankAccount(AbstractAccount):

    def __init__(self, person: Person, account_id, currency: Currency, account_number: str, account_type, balance: Decimal = Decimal(0)):
        if account_id is None:
            account_id = uuid()
        super().__init__(person, account_id, account_number, account_type, balance)
        self.currency = currency

    def validate_frozen(self):
        if self.account_status == AccountStatus.FROZEN:
            raise AccountFrozenError(f"Account {self.account_id} is frozen")

    def validate_closed(self):
        if self.account_status == AccountStatus.CLOSED:
            raise AccountClosedError(f"Account {self.account_id} is closed")

    def validate_currency(self, currency):
        if self.currency != currency:
            raise InvalidOperationError(f"Account {self.account_id} does not support currency {currency}")

    def validate_balance(self, amount:Decimal):
        if self.get_balance < amount:
            raise InsufficientFundsError(f"Account {self.account_id} does not have enough funds")

    def validate_amount(self, amount: Decimal):
        if not isinstance(amount, Decimal):
            raise InvalidOperationError("Сумма должна быть Decimal")

        if not amount.is_finite():
            raise InvalidOperationError("Сумма должна быть конечным числом")

        if amount < 0:
            raise InvalidOperationError("Сумма не может быть отрицательной")

    def deposit(self, amount, currency):
        self.validate_closed()
        self.validate_frozen()
        self.validate_currency(currency)
        self.validate_amount(amount)
        self._balance += amount

    def withdraw(self, amount, currency):
        self.validate_closed()
        self.validate_frozen()
        self.validate_currency(currency)
        self.validate_amount(amount)
        self.validate_balance(amount)
        self._balance -= amount

    def get_account_info(self):
        print(f"Account {self.account_id} has {self.get_balance} {self.currency}")

    def __str__(self):
        return f"Account {self.account_id} has {self.type} {self.person} {self.account_number[-4:]} {self.get_balance} {self.currency} {self.account_status}"
