import uuid
from decimal import Decimal

import pytest

from account_errors import AccountFrozenError
from currency import Currency
from models.abstract_account import AccountStatus, AccountType, Person
from models.bank_account import BankAccount


@pytest.fixture
def active_account() -> BankAccount:
    """Создаёт новый активный счёт для каждого теста."""
    return BankAccount(
        person=Person("Ivanov", 28, "somewhere", "01.01.2022"),
        account_id=uuid.uuid4(),
        currency=Currency.USD,
        account_type=AccountType.CURRENT,
        account_number="1234567890",
        balance=Decimal(1000),
    )


@pytest.fixture
def frozen_account() -> BankAccount:
    """Создаёт новый замороженный счёт для каждого теста."""
    account = BankAccount(
        person=Person("Ivanov", 28, "somewhere", "01.01.2022"),
        account_id=uuid.uuid4(),
        currency=Currency.USD,
        account_type=AccountType.CURRENT,
        account_number="1234567890",
    )
    account.account_status = AccountStatus.FROZEN
    return account


def test_valid_deposit(active_account: BankAccount) -> None:
    active_account.deposit(Decimal(100), currency=Currency.USD)

    assert active_account.get_balance == Decimal(1100)


def test_valid_withdraw(active_account: BankAccount) -> None:
    active_account.withdraw(Decimal(100), currency=Currency.USD)

    assert active_account.get_balance == Decimal(900)


def test_create_accounts(
    active_account: BankAccount, frozen_account: BankAccount
) -> None:
    assert active_account.account_status == AccountStatus.ACTIVE
    assert frozen_account.account_status == AccountStatus.FROZEN


def test_frozen_account_operations(frozen_account: BankAccount) -> None:
    with pytest.raises(AccountFrozenError):
        frozen_account.deposit(Decimal(100), currency=Currency.USD)

