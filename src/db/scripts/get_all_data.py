"""Print the contents of the DB"""
from src.lib.utils.db import get_all_users, get_all_products, get_all_interactions

def main():
    users = get_all_users()
    products = get_all_products()
    interactions = get_all_interactions()
    print(users if users else 'NO USERS.', end='\n\n')
    print(products if products else 'NO PRODUCTS.', end='\n\n')
    print(interactions if interactions else 'NO INTERACTIONS.')

if __name__ == '__main__':
    main()