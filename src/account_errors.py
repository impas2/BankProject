

class AccountError(Exception):
    pass
class AccountFrozenError(AccountError): pass

class AccountClosedError(AccountError): pass

class InvalidOperationError(AccountError): pass

class InsufficientFundsError(AccountError): pass
