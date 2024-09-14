import os, json, random, string, pandas as pd
from src.lib.modules.db import DBConn, User, Product
from src.lib.modules.logger import log
from src.lib.modules.constants import CREATIVE_LLM

if __name__ == '__main__':
    # Loading
    current_dir = os.path.dirname(os.path.abspath(__file__))
    products_json = os.path.join(current_dir, '../data/products.json')

    with open(products_json) as file:
        products_df = pd.DataFrame(json.load(file))
        owners = products_df['owner']

    # Adding
    with DBConn() as sess:
        # Add users first to prevent foreign key issues
        for owner in owners.unique():
            sess.add(User(
                username=owner, 
                password=''.join([random.choice(string.ascii_letters + string.digits) for _ in range(5)]),
                bio=CREATIVE_LLM.invoke(f'Write a bio for username "{owner}". Your response must only be the bio and nothing else.')
            ))
            log(f'[add_data_to_db.py] Added user "{owner}"', 'db')
        sess.commit()

        # Add products
        for row in products_df.iterrows():
            sess.add(Product(id=row[0], **row[1]))
            log(f'[add_data_to_db.py] Added product "{row[1]["name"]}"', 'db')