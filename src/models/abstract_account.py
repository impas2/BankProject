import abc
from decimal import Decimal
from enum import Enum
from uuid import UUID

from account_errors import InvalidOperationError
from currency import Currency


class Person:
    def __init__(self, name: str, age: int, address: str, birth_date: str) -> None:
        self.name = name
        self.age = age
        self.address = address
        self.birth_date = birth_date

    def __str__(self) -> str:
        return f"Person {self.name} {self.age} {self.address} {self.birth_date}"


class AccountStatus(Enum):
    ACTIVE = 0
    CLOSED = 1
    FROZEN = 2


class AccountType(Enum):
    CURRENT = 0
    SAVINGS = 1
    INVESTMENT = 2


class AbstractAccount(abc.ABC):
    def __init__(
        self,
        person: Person,
        account_id: UUID,
        account_number: str,
        account_type: AccountType,
        balance: Decimal = Decimal(0),
    ) -> None:
        if not isinstance(person, Person):
            raise InvalidOperationError("Владелец должен быть Person")

        if not isinstance(account_id, UUID):
            raise InvalidOperationError("Идентификатор счёта должен быть UUID")

        if not isinstance(account_number, str) or not account_number.strip():
            raise InvalidOperationError("Номер счёта должен быть непустой строкой")

        if not isinstance(account_type, AccountType):
            raise InvalidOperationError("Тип счёта должен быть AccountType")

        if not isinstance(balance, Decimal):
            raise InvalidOperationError("Баланс должен быть Decimal")

        if not balance.is_finite():
            raise InvalidOperationError("Баланс должен быть конечным числом")

        if balance < 0:
            raise InvalidOperationError("Баланс не может быть отрицательным")

        self.account_id = account_id
        self.account_number = account_number
        self.person = person
        self.type = account_type
        self._balance = balance
        self.account_status = AccountStatus.ACTIVE

    @abc.abstractmethod
    def deposit(self, amount: Decimal, currency: Currency) -> None:
        pass

    @abc.abstractmethod
    def withdraw(self, amount: Decimal, currency: Currency) -> None:
        pass

    @abc.abstractmethod
    def get_account_info(self) -> None:
        pass

    @property
    def account_status(self) -> AccountStatus:
        return self._account_status

    @account_status.setter
    def account_status(self, status: AccountStatus) -> None:
        if isinstance(status, AccountStatus):
            self._account_status = status

    @property
    def get_balance(self) -> Decimal:
        return self._balance

    @property
    def get_account_type(self) -> AccountType:
        return self.type
