from sqlalchemy import create_engine, Column, Integer, String, Float, VARCHAR, ARRAY, TEXT, ForeignKey, JSON
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB
from src.lib.modules.constants import USER, PASSWORD, HOST, PORT, DB

# Connection
class DBConn:
    """Simple interface to connect to the PostgreSQL DB"""
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
    bio = Column(TEXT())
    cart = Column(JSONB())
    ratings = Column(JSONB())

    def __init__(self, username=None, password=None, bio=None, cart=None, ratings=None):
        self.username, self.password, self.bio, self.cart, self.ratings = username, password, bio, cart, ratings
    
    def __repr__(self):
        return f"User('{self.username}')"


class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(511), nullable=False)
    description = Column(String)
    ratings = Column(ARRAY(Integer))
    price = Column(Float)
    discount = Column(Float)
    category = Column(String(255))
    owner = Column(String(255), ForeignKey('users.username'))
    reviews = Column(JSON)

    def __init__(self, id, name, description=None, ratings=None, price=None, discount=None, category=None, owner=None, reviews=None):
        self.id, self.name, self.description, self.ratings, self.price, self.discount, self.category, self.owner, self.reviews = id, name, description, ratings, price, discount, category, owner, reviews
    
    def __repr__(self):
        return f"Product('{self.name}')"