"""Print the contents of the DB"""
from src.lib.modules.data.db import DBConn, User, Product

if __name__ == '__main__':
    with DBConn() as sess:
        users = sess.query(User).all()
        products = sess.query(Product).all()
        
        if users:
            try: print(users)
            except: print('NO RESULTS.')
        else:
            print('NO USERS.')
        
        if products:
            try: print(products)
            except: print('NO RESULTS.')
        else:
            print('NO PRODUCTS.')