import abc
from decimal import Decimal
from enum import Enum
from uuid import UUID
from currency import Currency

class Person:
    def __init__(self, name, age, address, birth_date):
        self.name = name
        self.age = age
        self.address = address
        self.birth_date = birth_date


class AccountStatus(Enum):
    ACTIVE = 0
    CLOSED = 1
    FROZEN = 2

class AccountType(Enum):
    CURRENT = 0
    SAVINGS = 1

class AbstractAccount(abc.ABC):

    def __init__(self, person: Person, account_id: UUID, account_number: str, account_type: AccountType):
        self.account_id = account_id
        self.account_number = account_number
        self.person = person
        self.type = account_type
        self.__balance = Decimal(0)
        self.status = AccountStatus.ACTIVE

    @abc.abstractmethod
    def deposit(self, amount : Decimal, currency : Currency): pass

    @abc.abstractmethod
    def withdraw(self, amount : Decimal, currency : Currency): pass

    @abc.abstractmethod
    def get_account_info(self): pass

    @property
    def status(self):
        return self.status

    @status.setter
    def status(self, status):
        self.status = status

    @property
    def get_balance(self):
        return self.__balance
