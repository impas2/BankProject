from typing import Any

import pytest

from models.account.account_errors import AccountError
from models.client.client import Client
from models.client.client_errors import ClientAgeError

@pytest.fixture
def client_parameters() -> dict[str, Any]:
    return {"first_name": "Ivan", "last_name": "Ivanov", "age": 20, "accounts": [],
            "contacts": []}


class TestClient:

    def test_create_client(self, client_parameters: dict[str, Any]) -> None:
        client = Client(**client_parameters)

        assert client.first_name == client_parameters["first_name"]
        assert client.age == client_parameters["age"]

    @pytest.mark.parametrize("age", [-1, 0, 17])
    def test_client_age_validation(self, client_parameters, age) -> None:
        client_parameters.update(age=age)
        with pytest.raises(ClientAgeError):
            Client(**client_parameters)

    @pytest.mark.parametrize("accounts", [1, "string", None])
    def test_client_accounts_validation(self, client_parameters, accounts) -> None:
        client_parameters.update(accounts=accounts)
        with pytest.raises(AccountError):
            Client(**client_parameters)


