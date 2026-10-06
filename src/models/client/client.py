from enum import Enum
from uuid import uuid4

from models.account.abstract_account import Person
from models.account.account_errors import AccountError
from models.client.client_errors import ClientAgeError, ClientError


class ClientStatus(Enum):
    ACTIVE = 0
    BLOCKED = 1
    BLOCKED_BY_SECURITY = 2


class Client:
    def __init__(
        self,
        person: Person,
        accounts: list[str],
        contacts: list[str],
        secret: str,
        status: ClientStatus = ClientStatus.ACTIVE,
    ) -> None:
        if not isinstance(person, Person):
            raise ClientError("Client data must be Person")
        self.validate_age(person.age)
        self.validate_accounts(accounts)

        self.id = uuid4()
        self.person = person
        self._client_status = status
        self._accounts = accounts.copy()
        self.client_contact = contacts
        if not isinstance(secret, str):
            raise AccountError("Secret must be a string")
        if not isinstance(status, ClientStatus):
            raise AccountError("Client status must be an enum")
        self._client_status = status
        self._client_secret = secret
        self._auth_attempts = 3

    def reset_auth_attempts(self, attempts: int) -> None:
        self._auth_attempts = attempts
        if self._client_status == ClientStatus.BLOCKED_BY_SECURITY:
            self._client_status = ClientStatus.ACTIVE

    def validate_auth_attempts(self) -> bool:
        if self._client_status == ClientStatus.BLOCKED_BY_SECURITY:
            return False
        self._auth_attempts -= 1
        if self._auth_attempts <= 0:
            self._client_status = ClientStatus.BLOCKED_BY_SECURITY
            return False
        return True

    def validate_secret(self, secret: str) -> bool:
        if not isinstance(secret, str):
            raise AccountError("Secret must be a string")
        return self._client_secret == secret

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

    def add_client_accounts(self, accounts: list) -> None:
        if not isinstance(accounts, list):
            raise AccountError("Accounts must be a list")
        for account in accounts:
            if not isinstance(account, str):
                raise AccountError("Account number must be a string")
        self._accounts.extend(accounts)

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
        return self._client_status

    @client_status.setter
    def client_status(self, status: ClientStatus) -> None:
        if not isinstance(status, ClientStatus):
            raise AccountError("Client status must be an enum")
        self._client_status = status
