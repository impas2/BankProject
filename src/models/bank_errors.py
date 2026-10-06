class BankError(Exception):
    pass


class BankClosedError(BankError):
    pass


class BankTimeOperationError(BankError):
    pass


class ClientNotFound(BankError):
    pass


class ClientAlreadyExists(BankError):
    pass


class AccountNotFound(BankError):
    pass


class ClientNotActive(BankError):
    pass
