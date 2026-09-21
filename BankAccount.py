from AbstractAccount import Person
from uuid import UUID as uuid
from AbstractAccount import AbstractAccount
from currency import Currency
from AbstractAccount import AccountStatus
from AccountErrors import AccountClosedError, InvalidOperationError, InsufficientFundsError
from AccountErrors import AccountFrozenError


class BankAccount(AbstractAccount):

    def __init__(self, person: Person, account_id, currency: Currency, account_number: str, account_type):
        if account_id is None:
            account_id = uuid()
        super().__init__(person, account_id, account_number, account_type)
        self.currency = currency

    def validate_frozen(self):
        if self.status == AccountStatus.FROZEN:
            raise AccountFrozenError(f"Account {self.account_id} is frozen")

    def validate_closed(self):
        if self.status == AccountStatus.CLOSED:
            raise AccountClosedError(f"Account {self.account_id} is closed")

    def validate_currency(self, currency):
        if self.currency != currency:
            raise InvalidOperationError(f"Account {self.account_id} does not support currency {currency}")

    def validate_balance(self, amount):
        if self.get_balance < amount:
            raise InsufficientFundsError(f"Account {self.account_id} does not have enough funds")

    def deposit(self, amount, currency):
        self.validate_closed()
        self.validate_frozen()
        self.validate_currency(currency)
        self.__balance += amount

    def withdraw(self, amount, currency):
        self.validate_closed()
        self.validate_frozen()
        self.validate_currency(currency)
        self.validate_balance(amount)
        self.__balance -= amount

    def get_account_info(self):
        print(f"Account {self.account_id} has {self.get_balance} {self.currency}")

    def __str__(self):
        return f"Account {self.account_id} has {self.account_type}{self.person}{self.account_number}{self.get_balance} {self.currency} {self.status}"
