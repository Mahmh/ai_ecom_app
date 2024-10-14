from pydantic import BaseModel
from typing import Any, Union

# Models
class Credentials(BaseModel):
    """Accepts a username & password"""
    username: str
    password: str


class SecuredCredentials(BaseModel):
    """Makes the username & password able to be stored securely in the DB"""
    username: str
    password_hash: bytes
    salt: bytes


class UpdateBioInfo(Credentials):
    """Information to update a user's bio"""
    new_bio: str


# Exceptions
class UsernameTaken(Exception):
    """Exception for entering an existing username"""
    def __init__(self, username: str):
        super().__init__(f'Username "{username}" is already registered.')


class WrongCredentials(Exception):
    """Exception for entering wrong username or password"""
    def __init__(self, username: Union[str, None] = None, password: Union[str, None] = None):
        if username and password:
            super().__init__(f'Wrong credentials provided ({username=}, {password=})')
        else:
            super().__init__('Wrong credentials provided')


class NotOwner(Exception):
    """Exception for attempting to modify a product owned by another owner"""
    def __init__(self, username: str, product_id: int):
        super().__init__(f'User "{username}" is not the owner of product with ID {product_id}')


class NonExistent(Exception):
    """Exception for entering entities that don't exist"""
    def __init__(self, entity: str, identifier: Any):
        match entity:
            case 'user': 
                super().__init__(f'Account with username "{identifier}" is non-existent')
            case 'product': 
                super().__init__(f'Product with ID {identifier} is non-existent')