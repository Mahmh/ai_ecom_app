"""Supply the DB with synthetic data"""
import os, json, random, pandas as pd
from typing import Tuple, Union
from src.lib.data.db import Session, Product, Interaction
from src.lib.utils.db import end_session, get_hashed_img_filename, create_account, sanitize
from src.lib.utils.logger import log
from src.lib.types.db import Credentials
from src.lib.data.constants import CURRENT_DIR

def load_data() -> Tuple[Union[pd.DataFrame, pd.Series]]:
    products_json = os.path.join(CURRENT_DIR, '../../db/data/products.json')
    accounts_json = os.path.join(CURRENT_DIR, '../../db/data/accounts.json')
    with open(products_json) as file: products_df = pd.DataFrame(json.load(file))
    with open(accounts_json) as file: accounts_df = pd.DataFrame(json.load(file))
    return products_df, accounts_df


def add_users(accounts_df: pd.DataFrame, *, session) -> None:
    added = []
    for _, account in accounts_df.iterrows():
        username, password, bio = account.username, account.password, account.bio
        if username not in added:
            create_account(Credentials(username=username, password=password), bio=bio)
            added.append(username)
            log(f'[add_data_to_db.py] Added user "{username}"', 'db')
    session.commit()


def add_products(products_df: pd.DataFrame, *, session) -> None:
    for row in products_df.iterrows():
        owner = sanitize(row[1]['owner'])
        del row[1]['owner']
        session.add(Product(
            product_id=row[0], 
            **row[1],
            owner=owner,
            image_file=get_hashed_img_filename(row[1]['name'], row[0]) + '.webp'
        ))
        log(f'[add_data_to_db.py] Added product "{row[1]["name"]}"', 'db')
    session.commit()
    

def add_interactions(products_df: pd.DataFrame, accounts_df: pd.Series, *, session) -> None:
    interactions = [
        dict(
            username=urow,
            product_id=prow[0],
            rating=random.randint(1, 5),
            reviews=[random.choice(['Wow', 'It worked', 'Pretty good']) for _ in range(4)],
            in_cart=random.choice([True, False])
        )
        for urow, prow in zip(accounts_df['username'].unique(), products_df.iterrows())
    ]
    for row in interactions:
        session.add(Interaction(**row))
        log(f'[add_data_to_db.py] Added interaction "{row["username"]}" <-> {row["product_id"]}', 'db')


if __name__ == '__main__':
    # Init
    session = Session()
    # Load & add
    products_df, accounts_df = load_data()
    add_users(accounts_df, session=session)  # Add users first to prevent foreign key issues
    add_products(products_df, session=session)
    add_interactions(products_df, accounts_df, session=session)
    # Finish off
    end_session(session)