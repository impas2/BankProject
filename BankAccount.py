from AbstractAccount import AbstractAccount

class BankAccount(AbstractAccount):
    def __init__(self, name, age, person, account_id):
        super().__init__(person, account_id)

