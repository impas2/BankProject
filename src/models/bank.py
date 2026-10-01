from models.account.bank_account import BankAccount
from models.client.client import ClientStatus, Client


class Bank:

    def __init__(self, clients: list[Client], accounts: list[BankAccount]):
        self._clients = clients
        self._accounts = accounts
        self._suspicious_actions = {}

    def validate_client(self, client: Client):
        pass

    def add_client(self, client: Client) -> None:
        self._clients.append(client)

    def open_account(self, client: Client, account_type: str):
        pass

    def close_account(self, account_id: str):
        pass

    def freeze_account(self, account_id: str):
        pass

    def unfreeze_account(self, account_id: str):
        pass

    def authenticate_client(self, client_id: str, password: str):
        pass

    def search_accounts(self, client_id: str):
        pass

    def get_total_balance(self):
        pass

    def get_clients_ranking(self):
        pass

#Методы:
# - add_client()
# - open_account()
# - close_account()
# - freeze_account()
# - unfreeze_account()
# - authenticate_client()
# - search_accounts()
#3. Защита
# - 🔒 3 неверные попытки входа = блокировка
# - ⚠️ пометка подозрительных действий
# - 🌙 запрет операций с 00:00 до 05:00

# 4. Дополнительно
# - get_total_balance()
# - get_clients_ranking()


