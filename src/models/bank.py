import uuid
from datetime import datetime
from decimal import Decimal
from types import MappingProxyType
from typing import Optional

from models.account.abstract_account import AccountStatus, AccountType
from models.account.account_errors import AccountTypeNotAllowedError
from models.account.bank_account import BankAccount
from models.account.currency import Currency
from models.account.investment_account import InvestmentAccount
from models.account.premium_account import PremiumAccount
from models.account.savings_account import SavingsAccount
from models.bank_errors import BankTimeOperationError, ClientNotActive
from models.client.client import ClientStatus, Client


class BankActions:
    LOGIN = 0
    SEARCH_ACCOUNTS = 1
    GET_TOTAL_BALANCE = 2
    GET_CLIENTS_RANKING = 3

class SortDirection:
    ASC = 0
    DESC = 1


class Bank:

    def __init__(self, clients: list[Client], accounts: list[BankAccount]):
        self._clients = clients
        self._accounts = accounts
        self._suspicious_actions = {}
        self._authentications = {}

    def validate_client(self, client: Client) -> bool:
        return isinstance(client, Client)

    def validate_account_authentications(self, client_id: str) -> bool:
        return client_id in self._authentications

    def add_client(self, client: Client) -> None:
        self.validate_operation_time()
        self._clients.append(client)

    def open_account(self, client: Client, account_type: str, currency: Currency):
        self.validate_operation_time()
        if client not in self._clients:
            raise ClientNotActive("Client not found")
        if account_type not in AccountType:
            raise AccountTypeNotAllowedError("Invalid account type")
        if currency not in Currency:
            raise AccountTypeNotAllowedError("Invalid currency")
        if client.client_status != ClientStatus.ACTIVE:
            raise ClientNotActive("Client is not active")
        if not self.validate_account_authentications(client.id):
            raise ClientNotActive("Client is not authenticated")

        match account_type:
            case AccountType.SAVINGS:
                acc = SavingsAccount(client.person, uuid.uuid4(), currency,account_number=uuid.uuid4().__str__())
            case AccountType.INVESTMENT:
                acc =InvestmentAccount(client.person, uuid.uuid4(), currency,account_number=uuid.uuid4().__str__())
            case AccountType.CURRENT:
                acc =BankAccount(client.person, uuid.uuid4(), currency,account_number=uuid.uuid4().__str__())
            case AccountType.PREMIUM:
                acc =PremiumAccount(client.person, uuid.uuid4(), currency,account_number=uuid.uuid4().__str__())
            case _:
                raise AccountTypeNotAllowedError("Invalid account type")

        client.add_client_account(acc.account_number)
        self._accounts.append(acc)

    def close_account(self, account_id: str):
        self.validate_operation_time()
        for account in self._accounts:
            if account.account_id == uuid.UUID(account_id):
                account.account_status = AccountStatus.CLOSED
                return

    def freeze_account(self, account_id: str):
        self.validate_operation_time()
        for account in self._accounts:
            if account.account_id == uuid.UUID(account_id) and account.account_status == AccountStatus.ACTIVE:
                account.account_status = AccountStatus.FROZEN
                return

    def unfreeze_account(self, account_id: str):
        self.validate_operation_time()
        for account in self._accounts:
            if account.account_id == uuid.UUID(account_id) and account.account_status == AccountStatus.FROZEN:
                account.account_status = AccountStatus.ACTIVE
                return

    def authenticate_client(self, client_id: str, password: str) -> None:
        client = self.search_client(client_id)
        if client is None:
            self.add_suspicious_actions(client_id, "Login attempt with client not found")
            raise ClientNotActive("Client not found")

        self.validate_operation_time()
        self.validate_client_status(client)

        if client.validate_secret(password):
            client.reset_auth_attempts(3)
            self._authentications[client.id] = datetime.now()
        else:
            self.add_suspicious_actions(client_id, "Login attempt with wrong password")
            client.validate_auth_attempts()
            raise ClientNotActive("Wrong password")

    def search_client(self, client_id: str) -> Optional[Client]:
        for client in self._clients:
            if client.id == uuid.UUID(client_id):
                return client
        return None

    def search_accounts(self, account_id: str) -> Optional[BankAccount]:
        for account in self._accounts:
            if account.account_id == uuid.UUID(account_id):
                return account
        return None

    def search_accounts_by_num(self, account_number: str) -> Optional[BankAccount]:
        for account in self._accounts:
            if account.account_number == account_number:
                return account
        return None

    def get_total_balance(self) -> dict[Currency, Decimal]:
        total_balance = {}
        for account in self._accounts:
            if account.account_status == AccountStatus.ACTIVE:
                if account.currency not in total_balance:
                    total_balance[account.currency] = account.get_balance
                else:
                    total_balance[account.currency] += account.get_balance
        return total_balance

    def get_total_balance_with_all_actives(self) -> dict[Currency, Decimal]:
        total_balance = {}
        for account in self._accounts:
            if account.account_status == AccountStatus.ACTIVE:
                if account.currency not in total_balance:
                    total_balance[account.currency] = account.get_balance
                else:
                    total_balance[account.currency] += account.get_balance
        for account in self._accounts:
            if account.account_status == AccountStatus.ACTIVE:
                match account:
                    case InvestmentAccount():
                        if account.currency not in total_balance:
                            total_balance = account.get_portfolio_amount()
                        else:
                            total_balance[
                                account.currency] += account.get_portfolio_amount()

        return total_balance

    def get_clients_ranking(self, currency: Currency):
        self.validate_operation_time()
        clients_totals = {}
        for client in self._clients:
            client_total = 0
            client_accounts_num = client.get_accounts
            for client_account_num in client_accounts_num:
                account = self.search_accounts_by_num(client_account_num)
                if account is None:
                    continue
                if account.currency != currency:
                    continue
                client_total += account.get_balance
            clients_totals[client.id] = client_total
        return MappingProxyType(dict(sorted(clients_totals.items(), key=lambda item: item[1], reverse=True)))

    def validate_operation_time(self) -> None:
        if (datetime.now().hour < 5) or (datetime.now().hour > 23):
            raise BankTimeOperationError("Bank is closed")

    def validate_client_status(self, client: Client) -> None:
        if client.client_status != ClientStatus.ACTIVE:
            raise ClientNotActive("Client is not active")

    @property
    def suspicious_actions(self):
        return MappingProxyType(self._suspicious_actions.copy())

    def add_suspicious_actions(self, client_id: str, action: str) -> None:
        self._suspicious_actions[datetime.now()] = (client_id, action)
