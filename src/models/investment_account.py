
from models import bank_account


class investment_account(bank_account):
    def __init__(self, account_status: AccountStatus):
        self.account_status = account_status
