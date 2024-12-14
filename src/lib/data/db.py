from sqlalchemy import create_engine, Column, Integer, String, Float, Text, ARRAY, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import Any, Union
from pydantic import BaseModel
from src.lib.data.constants import ENGINE_URL

# Init
engine = create_engine(ENGINE_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()

# Tables
class UserData:
    def __init__(self, username, password_hash, salt, bio=''):
        self.username, self.password_hash, self.salt, self.bio = username, password_hash, salt, bio

    def __repr__(self):
        return f"User('{self.username}')"
    
    def detach(self):
        return UserData(self.username, self.password_hash, self.salt, self.bio)

class User(Base, UserData):
    __tablename__ = 'users'
    username = Column(String(255), nullable=False, primary_key=True)
    password_hash = Column(BYTEA, nullable=False)
    salt = Column(BYTEA, nullable=False)
    bio = Column(Text)



class ProductData:
    def __init__(self, product_id, name, owner, description='', price=None, discount=None, category=None, image_file=None):
        self.product_id, self.name, self.owner, self.description, self.price, self.discount, self.category, self.image_file = product_id, name, owner, description, price, discount, category, image_file
    
    def __repr__(self):
        return f"Product({self.product_id}, '{self.name}')"
    
    def detach(self):
        return ProductData(self.product_id, self.name, self.owner, self.description, self.price, self.discount, self.category, self.image_file)

class Product(Base, ProductData):
    __tablename__ = 'products'
    product_id = Column(Integer, nullable=False, primary_key=True, autoincrement=True)
    name = Column(String(511), nullable=False)
    description = Column(Text)
    image_file = Column(String(255))
    price = Column(Float)
    discount = Column(Float)
    category = Column(String(255))
    owner = Column(String(255), ForeignKey('users.username'))



class InteractionData:
    def __init__(self, username, product_id, rating=0, reviews=[], sentiments=[], in_cart=False):
        self.username, self.product_id, self.rating, self.reviews, self.sentiments, self.in_cart = username, product_id, rating, reviews, sentiments, in_cart
    
    def __repr__(self):
        return f"Interaction('{self.username}', {self.product_id})"
    
    def detach(self):
        return InteractionData(self.username, self.product_id, self.rating, self.reviews, self.sentiments, self.in_cart)

class Interaction(Base, InteractionData):
    __tablename__ = 'interactions'
    username = Column(String(255), ForeignKey('users.username'), nullable=False, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.product_id'), nullable=False, primary_key=True)
    rating = Column(Integer)
    reviews = Column(ARRAY(Text))
    sentiments = Column(ARRAY(Integer))
    in_cart = Column(Boolean)



# Pydantic Models
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