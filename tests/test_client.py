from typing import Any
from uuid import UUID, uuid4

import pytest

from models.account.abstract_account import Person
from models.account.account_errors import AccountError
from models.account.bank_account import BankAccount
from models.account.currency import Currency
from models.client.client import Client, ClientStatus
from models.client.client_errors import ClientAgeError, ClientError


@pytest.fixture
def client_parameters() -> dict[str, Any]:
    return {
        "person": Person("Ivan Ivanov", 20, "Moscow", "01.01.2006"),
        "accounts": [],
        "contacts": [],
        "secret": "test-secret",
    }


@pytest.fixture
def client(client_parameters: dict[str, Any]) -> Client:
    return Client(**client_parameters)


class TestClient:
    def test_create_client(self, client_parameters: dict[str, Any]) -> None:
        client = Client(**client_parameters)

        assert client.person is client_parameters["person"]
        assert client.person.name == "Ivan Ivanov"
        assert client.person.age == 20
        assert client.person.address == "Moscow"
        assert client.person.birth_date == "01.01.2006"
        assert isinstance(client.id, UUID)
        assert client.client_status is ClientStatus.ACTIVE

    def test_clients_receive_unique_ids(
        self, client_parameters: dict[str, Any]
    ) -> None:
        first = Client(**client_parameters)
        second = Client(**client_parameters)

        assert first.id != second.id

    @pytest.mark.parametrize("person", [None, "Ivan Ivanov", {"age": 20}])
    def test_client_rejects_data_that_is_not_person(
        self, client_parameters: dict[str, Any], person: Any
    ) -> None:
        client_parameters["person"] = person

        with pytest.raises(ClientError, match="Client data must be Person"):
            Client(**client_parameters)

    def test_client_accepts_person_aged_eighteen(
        self, client_parameters: dict[str, Any]
    ) -> None:
        person = Person("Ivan Ivanov", 18, "Moscow", "01.01.2008")
        client_parameters["person"] = person

        client = Client(**client_parameters)

        assert client.person is person

    def test_client_person_can_be_used_as_account_owner(
        self, client_parameters: dict[str, Any]
    ) -> None:
        client = Client(**client_parameters)

        account = BankAccount(
            person=client.person,
            account_id=uuid4(),
            currency=Currency.USD,
        )

        assert account.person is client.person

    @pytest.mark.parametrize("age", [-1, 0, 17])
    def test_client_age_validation(
        self, client_parameters: dict[str, Any], age: int
    ) -> None:
        client_parameters["person"].age = age
        with pytest.raises(ClientAgeError):
            Client(**client_parameters)

    @pytest.mark.parametrize("accounts", [1, "string", None, [123], ["valid", None]])
    def test_client_accounts_validation(
        self, client_parameters: dict[str, Any], accounts: Any
    ) -> None:
        client_parameters.update(accounts=accounts)
        with pytest.raises(AccountError):
            Client(**client_parameters)

    @pytest.mark.parametrize(
        ("field", "value"),
        [
            pytest.param("contacts", None, id="contacts-none"),
            pytest.param("contacts", "phone", id="contacts-string"),
            pytest.param("contacts", ("phone",), id="contacts-tuple"),
            pytest.param("contacts", [123], id="contact-not-string"),
            pytest.param("contacts", ["phone", None], id="mixed-contacts"),
            pytest.param("secret", None, id="secret-none"),
            pytest.param("secret", 123, id="secret-number"),
            pytest.param("secret", True, id="secret-boolean"),
            pytest.param("status", None, id="status-none"),
            pytest.param("status", "ACTIVE", id="status-string"),
            pytest.param("status", 0, id="status-enum-value"),
        ],
    )
    def test_constructor_rejects_invalid_fields(
        self, client_parameters: dict[str, Any], field: str, value: Any
    ) -> None:
        client_parameters[field] = value

        with pytest.raises(AccountError):
            Client(**client_parameters)

    def test_constructor_copies_account_and_contact_lists(
        self, client_parameters: dict[str, Any]
    ) -> None:
        accounts = ["account-1"]
        contacts = ["phone"]
        client = Client(
            **{**client_parameters, "accounts": accounts, "contacts": contacts}
        )

        accounts.append("external-account")
        contacts.clear()

        assert client.get_accounts == ("account-1",)
        assert client.client_contact == ("phone",)

    def test_account_and_contact_properties_return_immutable_snapshots(
        self, client: Client
    ) -> None:
        client.add_client_account("account-1")
        client.add_client_contact("phone")
        accounts = client.get_accounts
        contacts = client.client_contact

        with pytest.raises(TypeError):
            accounts[0] = "changed"
        with pytest.raises(TypeError):
            contacts[0] = "changed"

        client.add_client_account("account-2")
        client.add_client_contact("email")

        assert accounts == ("account-1",)
        assert contacts == ("phone",)
        assert client.get_accounts == ("account-1", "account-2")
        assert client.client_contact == ("phone", "email")

    def test_contact_setter_validates_before_replacing_contacts(
        self, client: Client
    ) -> None:
        client.client_contact = ["original"]

        with pytest.raises(AccountError):
            client.client_contact = ["valid", 123]

        assert client.client_contact == ("original",)

    def test_contact_setter_copies_the_new_list(self, client: Client) -> None:
        contacts = ["phone"]
        client.client_contact = contacts

        contacts.append("external")

        assert client.client_contact == ("phone",)

    def test_contacts_can_be_added_and_removed(self, client: Client) -> None:
        client.add_client_contact("phone")
        client.add_client_contact("email")

        client.remove_client_contact("phone")

        assert client.client_contact == ("email",)

    def test_accounts_can_be_added_and_removed(self, client: Client) -> None:
        client.add_client_account("account-1")
        client.add_client_accounts(["account-2", "account-3"])

        client.remove_client_account("account-2")

        assert client.get_accounts == ("account-1", "account-3")

    def test_invalid_account_batch_does_not_partially_update_client(
        self, client: Client
    ) -> None:
        client.add_client_account("original")

        with pytest.raises(AccountError):
            client.add_client_accounts(["valid", 123])

        assert client.get_accounts == ("original",)

    @pytest.mark.parametrize("status", list(ClientStatus))
    def test_status_setter_accepts_enum(
        self, client: Client, status: ClientStatus
    ) -> None:
        client.client_status = status

        assert client.client_status is status

    @pytest.mark.parametrize("status", [None, "BLOCKED", 1])
    def test_invalid_status_preserves_previous_status(
        self, client: Client, status: Any
    ) -> None:
        with pytest.raises(AccountError):
            client.client_status = status

        assert client.client_status is ClientStatus.ACTIVE

    @pytest.mark.parametrize(
        ("secret", "expected"),
        [("test-secret", True), ("wrong", False), ("", False), ("TEST-SECRET", False)],
    )
    def test_secret_comparison(
        self, client: Client, secret: str, expected: bool
    ) -> None:
        assert client.validate_secret(secret) is expected

    @pytest.mark.parametrize("secret", [None, 123, True])
    def test_secret_check_rejects_non_strings(
        self, client: Client, secret: Any
    ) -> None:
        with pytest.raises(AccountError):
            client.validate_secret(secret)

    def test_third_failed_attempt_blocks_client(self, client: Client) -> None:
        for _ in range(2):
            assert client.validate_auth_attempts() is True
            assert client.client_status is ClientStatus.ACTIVE

        assert client.validate_auth_attempts() is False
        assert client.client_status is ClientStatus.BLOCKED_BY_SECURITY
        assert client.validate_auth_attempts() is False
        assert client.client_status is ClientStatus.BLOCKED_BY_SECURITY

    def test_reset_restores_three_attempts(self, client: Client) -> None:
        client.validate_auth_attempts()
        client.validate_auth_attempts()

        client.reset_auth_attempts(3)

        assert client.validate_auth_attempts() is True
        assert client.validate_auth_attempts() is True
        assert client.validate_auth_attempts() is False
        assert client.client_status is ClientStatus.BLOCKED_BY_SECURITY

    def test_reset_clears_security_block(self, client: Client) -> None:
        for _ in range(3):
            client.validate_auth_attempts()

        client.reset_auth_attempts(3)

        assert client.client_status is ClientStatus.ACTIVE
        assert client.validate_auth_attempts() is True

    def test_reset_does_not_clear_manual_block(self, client: Client) -> None:
        client.client_status = ClientStatus.BLOCKED

        client.reset_auth_attempts(3)

        assert client.client_status is ClientStatus.BLOCKED
