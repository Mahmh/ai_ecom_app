from sqlalchemy import create_engine, Column, Integer, Float, VARCHAR, Text, ARRAY, Boolean, ForeignKey
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from src.lib.modules.data.constants import USER, PASSWORD, HOST, PORT, DB

# Connection
class DBConn:
    """Simple interface to connect to the app's PostgreSQL DB"""
    def __enter__(self):
        engine = create_engine(f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB}")
        self.session = sessionmaker(bind=engine)()
        return self.session

    def __exit__(self, *exc):
        try: self.session.commit()
        except Exception as e: self.session.rollback(); raise e
        finally: self.session.close()

# Tables
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    username = Column(VARCHAR(255), nullable=False, primary_key=True)
    password = Column(VARCHAR(255), nullable=False)
    bio = Column(Text())

    def __init__(self, username=None, password=None, bio=None, cart=None):
        self.username, self.password, self.bio, self.cart, self.ratings = username, password, bio, cart
    
    def __repr__(self):
        return f"User('{self.username}')"


class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer(), nullable=False, primary_key=True, autoincrement=True)
    name = Column(VARCHAR(511), nullable=False)
    description = Column(Text())
    price = Column(Float())
    discount = Column(Float())
    category = Column(VARCHAR(255))
    owner = Column(VARCHAR(255), ForeignKey('users.username'))

    def __init__(self, id, name, description=None, price=None, discount=None, category=None, owner=None):
        self.id, self.name, self.description, self.price, self.discount, self.category, self.owner = id, name, description, price, discount, category, owner
    
    def __repr__(self):
        return f"Product('{self.name}')"


class Interaction(Base):
    __tablename__ = 'interactions'
    username = Column(VARCHAR(255), ForeignKey('users.username'), nullable=False, primary_key=True)
    product_id = Column(VARCHAR(255), ForeignKey('products.id'), nullable=False, primary_key=True)
    rating = Column(Integer())
    reviews = Column(ARRAY(Text))
    in_cart = Column(Boolean())

    def __init__(self, username, product_id, rating=None, review=None, in_cart=None):
        self.username, self.product_id, self.rating, self.review, self.in_cart = id, username, product_id, rating, review, in_cart
    
    def __repr__(self):
        return f"Interaction('{self.username}', '{self.product_id}')"