
class ClientError(Exception):
    pass

class ClientNotFound(ClientError):
    pass

class ClientAlreadyExists(ClientError):
    pass

class ClientAgeError(ClientError):
    pass
