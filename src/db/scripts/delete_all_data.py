"""Make DB empty"""
from src.lib.modules.data.db import Session, User, Product, Interaction
from src.lib.modules.utils.db import end_session

def main():
    session = Session()
    users = session.query(User).all()
    products = session.query(Product).all()
    interactions = session.query(Interaction).all()
    for u in users: session.delete(u)
    for p in products: session.delete(p)
    for i in interactions: session.delete(i)
    end_session(session)

if __name__ == '__main__':
    main()