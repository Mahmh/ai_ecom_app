from sqlalchemy import create_engine, Column, Integer, String, Float, Text, ARRAY, Boolean, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base
from src.lib.modules.data.constants import ENGINE_URL

# Init
engine = create_engine(ENGINE_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()

# Tables
class UserData:
    def __init__(self, username, password, bio=''):
        self.username, self.password, self.bio = username, password, bio

    def __repr__(self):
        return f"User('{self.username}')"
    
    def detach(self):
        return UserData(self.username, self.password, self.bio)

class User(Base, UserData):
    __tablename__ = 'users'
    username = Column(String(255), nullable=False, primary_key=True)
    password = Column(String(255), nullable=False)
    bio = Column(Text)



class ProductData:
    def __init__(self, product_id, name, owner, description='', price=None, discount=None, category=None):
        self.product_id, self.name, self.owner, self.description, self.price, self.discount, self.category = product_id, name, owner, description, price, discount, category
    
    def __repr__(self):
        return f"Product({self.product_id}, '{self.name}')"
    
    def detach(self):
        return ProductData(self.product_id, self.name, self.owner, self.description, self.price, self.discount, self.category)

class Product(Base, ProductData):
    __tablename__ = 'products'
    product_id = Column(Integer, nullable=False, primary_key=True, autoincrement=True)
    name = Column(String(511), nullable=False)
    description = Column(Text)
    price = Column(Float)
    discount = Column(Float)
    category = Column(String(255))
    owner = Column(String(255), ForeignKey('users.username'))



class InteractionData:
    def __init__(self, username, product_id, rating=0, reviews=[], in_cart=False):
        self.username, self.product_id, self.rating, self.reviews, self.in_cart = username, product_id, rating, reviews, in_cart
    
    def __repr__(self):
        return f"Interaction('{self.username}', {self.product_id})"
    
    def detach(self):
        return InteractionData(self.username, self.product_id, self.rating, self.reviews, self.in_cart)

class Interaction(Base, InteractionData):
    __tablename__ = 'interactions'
    username = Column(String(255), ForeignKey('users.username'), nullable=False, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.product_id'), nullable=False, primary_key=True)
    rating = Column(Integer)
    reviews = Column(ARRAY(Text))
    in_cart = Column(Boolean)