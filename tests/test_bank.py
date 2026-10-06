from collections.abc import Callable
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import uuid4

import pytest

from models import bank as bank_module
from models.account.abstract_account import AccountStatus, AccountType, Person
from models.account.account_errors import (
    AccountClosedError,
    AccountFrozenError,
    AccountTypeNotAllowedError,
)
from models.account.bank_account import BankAccount
from models.account.currency import Currency
from models.account.investment_account import InvestmentAccount, InvestmentActive
from models.account.premium_account import PremiumAccount
from models.account.savings_account import SavingsAccount
from models.bank import Bank
from models.bank_errors import BankTimeOperationError, ClientNotActive
from models.client.client import Client, ClientStatus


@pytest.fixture(autouse=True)
def bank_clock(monkeypatch: pytest.MonkeyPatch) -> Callable[[datetime], None]:
    """По умолчанию в банке полдень; ночные тесты сами переводят часы."""
    current = datetime(2026, 10, 6, 12)

    class ControlledDateTime:
        @classmethod
        def now(cls) -> datetime:
            nonlocal current
            result = current
            # События получают разные метки времени даже при быстром запуске.
            current += timedelta(microseconds=1)
            return result

    def set_time(value: datetime) -> None:
        nonlocal current
        current = value

    monkeypatch.setattr(bank_module, "datetime", ControlledDateTime)
    return set_time


@pytest.fixture
def account_data() -> dict[str, Any]:
    return {
        "person": Person("Ivanov", 28, "somewhere", "01.01.2022"),
        "account_id": uuid4(),
        "currency": Currency.USD,
        "account_number": "001234567890",
        "account_type": AccountType.CURRENT,
        "balance": Decimal("100.50"),
    }


@pytest.fixture
def client_data() -> dict[str, Any]:
    return {
        "person": Person("Ivan Ivanov", 20, "Moscow", "01.01.2006"),
        "accounts": [],
        "contacts": [],
        "secret": "test-secret",
    }


@pytest.fixture
def client(client_data: dict[str, Any]) -> Client:
    return Client(**client_data)


@pytest.fixture
def bank(client: Client) -> Bank:
    return Bank(clients=[client], accounts=[])


@pytest.fixture
def registered_account(client: Client, account_data: dict[str, Any]) -> BankAccount:
    return BankAccount(**{**account_data, "person": client.person})


@pytest.fixture
def bank_with_account(client: Client, registered_account: BankAccount) -> Bank:
    client.add_client_account(registered_account.account_number)
    return Bank(clients=[client], accounts=[registered_account])


def make_accounts(account_data: dict[str, Any]) -> list[BankAccount]:
    cases = [
        ("001234567890", Currency.EUR, AccountStatus.ACTIVE),
        ("111234567890", Currency.USD, AccountStatus.FROZEN),
        ("222234567890", Currency.USD, AccountStatus.CLOSED),
        ("333234567890", Currency.EUR, AccountStatus.FROZEN),
        ("444234567890", Currency.RUB, AccountStatus.ACTIVE),
        ("555234567890", Currency.USD, AccountStatus.ACTIVE),
    ]
    accounts = []
    for number, currency, status in cases:
        account = BankAccount(
            **{
                **account_data,
                "account_id": uuid4(),
                "account_number": number,
                "currency": currency,
            }
        )
        account.account_status = status
        accounts.append(account)
    return accounts


def make_clients(client_data: dict[str, Any]) -> list[Client]:
    client1 = Client(**client_data)
    client1.add_client_accounts(["555234567890", "444234567890"])
    client2 = Client(**client_data)
    client2.add_client_accounts(["333234567890", "222234567890"])
    client3 = Client(**client_data)
    client3.add_client_accounts(["111234567890", "001234567890"])
    client4 = Client(**client_data)
    return [client1, client2, client3, client4]


@pytest.fixture
def ranking_clients(client_data: dict[str, Any]) -> dict[str, Client]:
    person = client_data["person"]
    return {
        name: Client(
            **{
                **client_data,
                "person": Person(name, person.age, person.address, person.birth_date),
            }
        )
        for name in ("Ivan", "Anna", "Petr")
    }


@pytest.fixture
def ranking_bank(ranking_clients: dict[str, Client]) -> Bank:
    account_cases = [
        ("Ivan", Currency.USD, "100.50"),
        ("Ivan", Currency.USD, "20.25"),
        ("Ivan", Currency.EUR, "900.00"),
        ("Petr", Currency.USD, "300.00"),
        ("Petr", Currency.EUR, "50.00"),
    ]
    accounts = []
    for name, currency, balance in account_cases:
        client = ranking_clients[name]
        account = BankAccount(
            person=client.person,
            account_id=uuid4(),
            currency=currency,
            balance=Decimal(balance),
        )
        accounts.append(account)
        client.add_client_account(account.account_number)

    # Anna без счетов стоит в середине, чтобы выявить отсутствие сортировки.
    return Bank(clients=list(ranking_clients.values()), accounts=accounts)


class TestBank:
    def test_bank_creation(
        self, client_data: dict[str, Any], account_data: dict[str, Any]
    ) -> None:
        bank = Bank(make_clients(client_data), make_accounts(account_data))

        total_balance = bank.get_total_balance()

        assert total_balance == {
            Currency.EUR: Decimal("100.50"),
            Currency.USD: Decimal("100.50"),
            Currency.RUB: Decimal("100.50"),
        }

    @pytest.mark.parametrize(
        ("currency", "expected_totals"),
        [
            pytest.param(
                Currency.USD,
                {"Ivan": "120.75", "Petr": "300.00", "Anna": "0"},
                id="usd-sums-multiple-accounts",
            ),
            pytest.param(
                Currency.EUR,
                {"Ivan": "900.00", "Petr": "50.00", "Anna": "0"},
                id="eur-excludes-usd",
            ),
            pytest.param(
                Currency.KZT,
                {"Ivan": "0", "Petr": "0", "Anna": "0"},
                id="no-accounts-in-requested-currency",
            ),
        ],
    )
    def test_get_clients_ranking_sums_accounts_in_requested_currency(
        self,
        ranking_bank: Bank,
        ranking_clients: dict[str, Client],
        currency: Currency,
        expected_totals: dict[str, str],
    ) -> None:
        ranking = ranking_bank.get_clients_ranking(currency)

        assert ranking == {
            ranking_clients[name].id: Decimal(total)
            for name, total in expected_totals.items()
        }

    @pytest.mark.parametrize(
        ("currency", "expected_names"),
        [
            pytest.param(Currency.USD, ("Petr", "Ivan", "Anna"), id="usd-order"),
            pytest.param(Currency.EUR, ("Ivan", "Petr", "Anna"), id="eur-order"),
        ],
    )
    def test_get_clients_ranking_orders_clients_by_total_descending(
        self,
        ranking_bank: Bank,
        ranking_clients: dict[str, Client],
        currency: Currency,
        expected_names: tuple[str, ...],
    ) -> None:
        ranking = ranking_bank.get_clients_ranking(currency)

        # Равенство словарей не проверяет порядок ключей, поэтому нужен список.
        assert list(ranking) == [ranking_clients[name].id for name in expected_names]

    def test_get_clients_ranking_returns_empty_result_for_empty_bank(self) -> None:
        bank = Bank(clients=[], accounts=[])

        assert bank.get_clients_ranking(Currency.USD) == {}

    def test_add_client_makes_client_searchable(self, client: Client) -> None:
        bank = Bank(clients=[], accounts=[])

        bank.add_client(client)

        assert bank.search_client(str(client.id)) is client

    def test_search_returns_none_for_unknown_ids(self, bank: Bank) -> None:
        unknown_id = str(uuid4())

        assert bank.search_client(unknown_id) is None
        assert bank.search_accounts(unknown_id) is None
        assert bank.search_accounts_by_num("missing-number") is None

    def test_search_account_accepts_string_uuid(
        self, bank_with_account: Bank, registered_account: BankAccount
    ) -> None:
        assert (
            bank_with_account.search_accounts(str(registered_account.account_id))
            is registered_account
        )
        assert (
            bank_with_account.search_accounts_by_num(registered_account.account_number)
            is registered_account
        )

    @pytest.mark.parametrize(
        ("account_type", "expected_class"),
        [
            (AccountType.CURRENT, BankAccount),
            (AccountType.SAVINGS, SavingsAccount),
            (AccountType.PREMIUM, PremiumAccount),
            (AccountType.INVESTMENT, InvestmentAccount),
        ],
    )
    def test_authenticated_client_can_open_each_account_type(
        self,
        bank: Bank,
        client: Client,
        account_type: AccountType,
        expected_class: type[BankAccount],
    ) -> None:
        bank.authenticate_client(str(client.id), "test-secret")

        bank.open_account(client, account_type, Currency.USD)

        assert len(client.get_accounts) == 1
        account = bank.search_accounts_by_num(client.get_accounts[0])
        assert isinstance(account, expected_class)
        assert account.get_account_type is account_type
        assert account.person is client.person
        assert account.currency is Currency.USD
        assert account.get_balance == Decimal("0")
        assert account.account_status is AccountStatus.ACTIVE

    def test_opened_accounts_receive_unique_numbers_and_ids(
        self, bank: Bank, client: Client
    ) -> None:
        bank.authenticate_client(str(client.id), "test-secret")

        bank.open_account(client, AccountType.CURRENT, Currency.USD)
        bank.open_account(client, AccountType.CURRENT, Currency.EUR)

        assert len(set(client.get_accounts)) == 2
        first, second = [
            bank.search_accounts_by_num(number) for number in client.get_accounts
        ]
        assert first is not None and second is not None
        assert first.account_id != second.account_id

    def test_open_requires_authentication(self, bank: Bank, client: Client) -> None:
        with pytest.raises(ClientNotActive, match="not authenticated"):
            bank.open_account(client, AccountType.CURRENT, Currency.USD)

        assert client.get_accounts == ()
        assert bank.get_total_balance() == {}

    def test_open_rejects_unregistered_client(
        self, bank: Bank, client_data: dict[str, Any]
    ) -> None:
        stranger = Client(**client_data)

        with pytest.raises(ClientNotActive, match="not found"):
            bank.open_account(stranger, AccountType.CURRENT, Currency.USD)

        assert stranger.get_accounts == ()
        assert bank.get_total_balance() == {}

    @pytest.mark.parametrize(
        "status", [ClientStatus.BLOCKED, ClientStatus.BLOCKED_BY_SECURITY]
    )
    def test_blocked_client_cannot_open_account_even_after_login(
        self, bank: Bank, client: Client, status: ClientStatus
    ) -> None:
        bank.authenticate_client(str(client.id), "test-secret")
        client.client_status = status

        with pytest.raises(ClientNotActive):
            bank.open_account(client, AccountType.CURRENT, Currency.USD)

        assert client.get_accounts == ()

    @pytest.mark.parametrize(
        ("account_type", "currency"),
        [
            pytest.param(None, Currency.USD, id="missing-account-type"),
            pytest.param("crypto", Currency.USD, id="unknown-account-type"),
            pytest.param(AccountType.CURRENT, None, id="missing-currency"),
            pytest.param(AccountType.CURRENT, "BTC", id="unknown-currency"),
        ],
    )
    def test_open_rejects_invalid_parameters_without_adding_account(
        self, bank: Bank, client: Client, account_type: Any, currency: Any
    ) -> None:
        bank.authenticate_client(str(client.id), "test-secret")

        with pytest.raises(AccountTypeNotAllowedError):
            bank.open_account(client, account_type, currency)

        assert client.get_accounts == ()
        assert bank.get_total_balance() == {}

    def test_wrong_password_does_not_authorize_client(
        self, bank: Bank, client: Client
    ) -> None:
        with pytest.raises(ClientNotActive):
            bank.authenticate_client(str(client.id), "wrong")

        with pytest.raises(ClientNotActive, match="not authenticated"):
            bank.open_account(client, AccountType.CURRENT, Currency.USD)
        assert client.client_status is ClientStatus.ACTIVE
        assert len(bank.suspicious_actions) == 1
        actor_id, action = next(iter(bank.suspicious_actions.values()))
        assert actor_id == str(client.id)
        assert isinstance(action, str) and action

    def test_third_wrong_password_blocks_further_login(
        self, bank: Bank, client: Client
    ) -> None:
        for _ in range(2):
            with pytest.raises(ClientNotActive):
                bank.authenticate_client(str(client.id), "wrong")
            assert client.client_status is ClientStatus.ACTIVE

        with pytest.raises(ClientNotActive):
            bank.authenticate_client(str(client.id), "wrong")
        assert client.client_status is ClientStatus.BLOCKED_BY_SECURITY
        assert len(bank.suspicious_actions) == 3

        with pytest.raises(ClientNotActive):
            bank.authenticate_client(str(client.id), "test-secret")
        with pytest.raises(ClientNotActive):
            bank.open_account(client, AccountType.CURRENT, Currency.USD)
        assert client.get_accounts == ()

    def test_successful_login_resets_failed_attempts(
        self, bank: Bank, client: Client
    ) -> None:
        for _ in range(2):
            with pytest.raises(ClientNotActive):
                bank.authenticate_client(str(client.id), "wrong")

        bank.authenticate_client(str(client.id), "test-secret")

        for _ in range(2):
            with pytest.raises(ClientNotActive):
                bank.authenticate_client(str(client.id), "wrong")
            assert client.client_status is ClientStatus.ACTIVE
        with pytest.raises(ClientNotActive):
            bank.authenticate_client(str(client.id), "wrong")
        assert client.client_status is ClientStatus.BLOCKED_BY_SECURITY

    @pytest.mark.parametrize(
        "status", [ClientStatus.BLOCKED, ClientStatus.BLOCKED_BY_SECURITY]
    )
    def test_blocked_client_cannot_authenticate(
        self, bank: Bank, client: Client, status: ClientStatus
    ) -> None:
        client.client_status = status

        with pytest.raises(ClientNotActive):
            bank.authenticate_client(str(client.id), "test-secret")

        assert client.client_status is status

    def test_unknown_client_login_is_logged(self, bank: Bank) -> None:
        unknown_id = str(uuid4())

        with pytest.raises(ClientNotActive):
            bank.authenticate_client(unknown_id, "wrong")

        assert len(bank.suspicious_actions) == 1
        assert next(iter(bank.suspicious_actions.values()))[0] == unknown_id

    @pytest.mark.parametrize(
        ("method", "status", "error"),
        [
            ("freeze_account", AccountStatus.FROZEN, AccountFrozenError),
            ("close_account", AccountStatus.CLOSED, AccountClosedError),
        ],
    )
    def test_status_change_by_string_uuid_blocks_withdrawal(
        self,
        bank_with_account: Bank,
        registered_account: BankAccount,
        method: str,
        status: AccountStatus,
        error: type[Exception],
    ) -> None:
        balance_before = registered_account.get_balance

        getattr(bank_with_account, method)(str(registered_account.account_id))

        assert registered_account.account_status is status
        with pytest.raises(error):
            registered_account.withdraw(Decimal("1"), Currency.USD)
        assert registered_account.get_balance == balance_before

    def test_unfreeze_restores_withdrawal(
        self, bank_with_account: Bank, registered_account: BankAccount
    ) -> None:
        account_id = str(registered_account.account_id)
        bank_with_account.freeze_account(account_id)
        balance_before = registered_account.get_balance

        bank_with_account.unfreeze_account(account_id)
        registered_account.withdraw(Decimal("1"), Currency.USD)

        assert registered_account.account_status is AccountStatus.ACTIVE
        assert registered_account.get_balance == balance_before - Decimal("1")

    @pytest.mark.parametrize("method", ["freeze_account", "unfreeze_account"])
    def test_closed_account_cannot_be_reactivated(
        self,
        bank_with_account: Bank,
        registered_account: BankAccount,
        method: str,
    ) -> None:
        account_id = str(registered_account.account_id)
        bank_with_account.close_account(account_id)

        getattr(bank_with_account, method)(account_id)

        assert registered_account.account_status is AccountStatus.CLOSED
        with pytest.raises(AccountClosedError):
            registered_account.deposit(Decimal("1"), Currency.USD)

    @pytest.mark.parametrize(
        "operation",
        ["add", "open", "close", "freeze", "unfreeze", "authenticate", "ranking"],
    )
    def test_night_operations_are_rejected_without_changing_accounts(
        self,
        bank_with_account: Bank,
        registered_account: BankAccount,
        client: Client,
        client_data: dict[str, Any],
        bank_clock: Callable[[datetime], None],
        operation: str,
    ) -> None:
        bank = bank_with_account
        bank.authenticate_client(str(client.id), "test-secret")
        stranger = Client(**client_data)
        account_id = str(registered_account.account_id)
        numbers_before = client.get_accounts
        balance_before = registered_account.get_balance
        operations = {
            "add": lambda: bank.add_client(stranger),
            "open": lambda: bank.open_account(
                client, AccountType.CURRENT, Currency.USD
            ),
            "close": lambda: bank.close_account(account_id),
            "freeze": lambda: bank.freeze_account(account_id),
            "unfreeze": lambda: bank.unfreeze_account(account_id),
            "authenticate": lambda: bank.authenticate_client(
                str(client.id), "test-secret"
            ),
            "ranking": lambda: bank.get_clients_ranking(Currency.USD),
        }
        bank_clock(datetime(2026, 10, 6, 2))

        with pytest.raises(BankTimeOperationError):
            operations[operation]()

        assert client.get_accounts == numbers_before
        assert registered_account.get_balance == balance_before
        assert registered_account.account_status is AccountStatus.ACTIVE
        assert bank.search_client(str(stranger.id)) is None

    @pytest.mark.parametrize("hour, minute, second", [(0, 0, 0), (4, 59, 59)])
    def test_time_guard_rejects_night_boundaries(
        self,
        bank: Bank,
        bank_clock: Callable[[datetime], None],
        hour: int,
        minute: int,
        second: int,
    ) -> None:
        bank_clock(datetime(2026, 10, 6, hour, minute, second))

        with pytest.raises(BankTimeOperationError):
            bank.validate_operation_time()

    @pytest.mark.parametrize("hour, minute, second", [(5, 0, 0), (23, 59, 59)])
    def test_time_guard_accepts_day_boundaries(
        self,
        bank: Bank,
        bank_clock: Callable[[datetime], None],
        hour: int,
        minute: int,
        second: int,
    ) -> None:
        bank_clock(datetime(2026, 10, 6, hour, minute, second))

        bank.validate_operation_time()

    def test_empty_bank_has_no_balances(self) -> None:
        bank = Bank(clients=[], accounts=[])

        assert bank.get_total_balance() == {}
        assert bank.get_total_balance_with_all_actives() == {}

    def test_total_assets_include_invested_money_without_double_counting(
        self, client: Client, registered_account: BankAccount
    ) -> None:
        investment = InvestmentAccount(client.person, uuid4(), Currency.USD)
        investment.deposit(Decimal("1000"), Currency.USD)
        investment.invest(InvestmentActive.STOCKS, Decimal("400"))
        bank = Bank(clients=[client], accounts=[registered_account, investment])

        assert bank.get_total_balance() == {Currency.USD: Decimal("700.50")}
        assert bank.get_total_balance_with_all_actives() == {
            Currency.USD: Decimal("1100.50")
        }

    def test_ranking_skips_missing_account_numbers(
        self, bank_with_account: Bank, client: Client, registered_account: BankAccount
    ) -> None:
        client.add_client_account("missing-number")

        ranking = bank_with_account.get_clients_ranking(Currency.USD)

        assert ranking == {client.id: registered_account.get_balance}

    def test_ranking_is_an_immutable_snapshot(
        self, bank_with_account: Bank, client: Client, registered_account: BankAccount
    ) -> None:
        ranking = bank_with_account.get_clients_ranking(Currency.USD)
        balance_before = registered_account.get_balance

        with pytest.raises(TypeError):
            ranking[client.id] = Decimal("999")
        registered_account.deposit(Decimal("10"), Currency.USD)

        assert ranking[client.id] == balance_before
        assert bank_with_account.get_clients_ranking(Currency.USD)[client.id] == (
            balance_before + Decimal("10")
        )

    def test_suspicious_actions_return_an_immutable_snapshot(
        self, bank: Bank, client: Client
    ) -> None:
        bank.add_suspicious_actions(str(client.id), "first event")
        snapshot = bank.suspicious_actions
        timestamp = next(iter(snapshot))

        with pytest.raises(TypeError):
            snapshot[timestamp] = (str(client.id), "changed")
        with pytest.raises(TypeError):
            snapshot[timestamp][1] = "changed"
        bank.add_suspicious_actions(str(client.id), "second event")

        assert snapshot == {timestamp: (str(client.id), "first event")}
        assert list(bank.suspicious_actions.values()) == [
            (str(client.id), "first event"),
            (str(client.id), "second event"),
        ]
