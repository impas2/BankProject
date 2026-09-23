import uuid
from decimal import Decimal

import pytest

from abstract_account import Person, AccountType, AccountStatus
from account_errors import AccountFrozenError
from bank_account import BankAccount
from currency import Currency

@pytest.fixture
def account_active() -> BankAccount:
    """По умолчанию pytest создаёт новый заказ для каждого тестового случая."""
    return BankAccount(person=Person("Ivanov",
                                     28,
                                     "somewhere",
                                     "01.01.2022"),
                       account_id=uuid.uuid4(),
                       currency=Currency.USD,
                       account_type=AccountType.CURRENT,
                       account_number="1234567890",
                       balance=Decimal(1000))


@pytest.fixture
def account_frozen() -> BankAccount:
    frozen_account = BankAccount(person=Person("Ivanov",
                                               28,
                                               "somewhere",
                                               "01.01.2022"),
                                 account_id=uuid.uuid4(),
                                 currency=Currency.USD,
                                 account_type=AccountType.CURRENT,
                                 account_number="1234567890")
    frozen_account.account_status = AccountStatus.FROZEN
    return frozen_account


def test_valid_deposit(account_active) -> None:
    account1 = account_active
    account1.deposit(Decimal(100), currency=Currency.USD)

    assert account1.get_balance == Decimal(1100)

def test_valid_withdraw(account_active) -> None:
    account1 = account_active
    account1.withdraw(Decimal(100), currency=Currency.USD)

    assert account1.get_balance == Decimal(900)

def test_create_accounts(account_active, account_frozen) -> None:
    account1 = account_active
    account2 = account_frozen

    assert account1.account_status == AccountStatus.ACTIVE
    assert account2.account_status == AccountStatus.FROZEN

def test_frozen_account_operations(account_frozen) -> None:
    account1 = account_frozen

    with pytest.raises(AccountFrozenError):
        account1.deposit(Decimal(100), currency=Currency.USD)
