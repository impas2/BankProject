import abc
from decimal import Decimal
from enum import Enum

class AbstractAccount(abc.ABC):

    def __init__(self,person, account_id):
        self.account_id = account_id
        self.person = person
        self.__balance = Decimal(0)
        self.status = AccountStatus.ACTIVE

    @abc.abstractmethod
    def deposit(self, amount):pass
    @abc.abstractmethod
    def withdraw(self, amount):pass
    @abc.abstractmethod
    def get_account_info(self):pass

    @property
    def status(self):
        return self.status
    @status.setter
    def status(self, status):
        self.status = status

    @property
    def get_balance(self):
        return self.__balance
    def add_balance(self, amount):
        self.__balance = self.__balance + Decimal(amount)
    def subtract_balance(self, amount):
        self.__balance = self.__balance - Decimal(amount)

class Person:
    def __init__(self,name,age,address,birth_date):
        self.name = name
        self.age = age
        self.address = address
        self.birth_date = birth_date


class AccountStatus(Enum):
    ACTIVE = 0
    CLOSED = 1
    FROZEN = 2
