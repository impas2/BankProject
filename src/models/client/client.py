from enum import Enum
from uuid import uuid4, UUID

from models.account.account_errors import AccountError
from models.client.client_errors import ClientAgeError

class ClientStatus(Enum):
    ACTIVE = 0
    BLOCKED = 1

class Client:

    def __init__(self, first_name: str, last_name: str, age: int, accounts: list[str],
                 contacts: list[str], secret:str, status: ClientStatus = ClientStatus.ACTIVE):
        self.validate_age(age)
        self.validate_accounts(accounts)

        self.id = uuid4()
        self.first_name = first_name
        self.last_name = last_name
        self.age = age
        self._client_status = status
        self._accounts = accounts.copy()
        self._contacts = contacts.copy()
        self._client_status = status
        self._client_secret = secret

    def validate_age(self, age: int) -> None:
        if age < 18:
            raise ClientAgeError("Client must be at least 18 years old")

    def validate_accounts(self, accounts: list) -> None:
        if not isinstance(accounts, list):
            raise AccountError("Accounts list must be a list")
        else:
            for account in accounts:
                if not isinstance(account, str):
                    raise AccountError("Account must be a string")

    @property
    def get_accounts(self) -> tuple[str, ...]:
        return tuple(self._accounts)

    @property
    def client_contact(self) -> tuple[str, ...]:
        return tuple(self._contacts)

    @client_contact.setter
    def client_contact(self, contacts: list[str]) -> None:
        if not isinstance(contacts, list):
            raise AccountError("Contacts list must be a list")
        else:
            for contact in contacts:
                if not isinstance(contact, str):
                    raise AccountError("Contact must be a string")
        self._contacts = contacts.copy()

    def add_client_contact(self, contact: str) -> None:
        if not isinstance(contact, str):
            raise AccountError("Contact must be a string")
        self._contacts.append(contact)

    def add_client_account(self, account: str) -> None:
        if not isinstance(account, str):
            raise AccountError("Account must be a string")
        self._accounts.append(account)

    def remove_client_account(self, account: str) -> None:
        if not isinstance(account, str):
            raise AccountError("Account must be a string")
        self._accounts.remove(account)

    def remove_client_contact(self, contact: str) -> None:
        if not isinstance(contact, str):
            raise AccountError("Contact must be a string")
        self._contacts.remove(contact)

    @property
    def client_status(self) -> ClientStatus:
        return self.client_status

    @client_status.setter
    def client_status(self, status: ClientStatus) -> None:
        if not isinstance(status, ClientStatus):
            raise AccountError("Client status must be an enum")
        self.client_status = status
