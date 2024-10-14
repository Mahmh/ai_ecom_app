"""Supply the DB with synthetic data"""
import os, json, random, string, pandas as pd, time, multiprocessing as mp
from typing import Tuple, Any
from src.lib.data.db import Session, Product, Interaction
from src.lib.utils.db import end_session, get_hashed_img_filename, create_account
from src.lib.utils.logger import log
from src.lib.types.db import Credentials
from src.lib.data.constants import CURRENT_DIR, CREATIVE_LLM

def load_data() -> Tuple[pd.DataFrame]:
    products_json = os.path.join(CURRENT_DIR, '../../db/data/products.json')

    with open(products_json) as file:
        products_df = pd.DataFrame(json.load(file))
        owners = products_df['owner']
    return products_df, owners


def add_user(owner: str, lock: Any, *, session) -> None:
    user_cred = Credentials(
        username=owner,
        password=''.join([random.choice(string.ascii_letters + string.digits) for _ in range(5)]),
    )
    #user_bio = CREATIVE_LLM.invoke(f'Write a bio for username "{owner}". Your response must only be the bio and nothing else.')
    with lock:
        # create_account(user_cred, bio=user_bio)
        create_account(user_cred)
        session.commit()
        log(f'[add_data_to_db.py] Added user "{owner}"', 'db')


def add_users(owners: pd.DataFrame, *, session) -> None:
    processes = []
    lock = mp.Lock()
    for owner in owners.unique():
        p = mp.Process(target=add_user, args=(owner, lock), kwargs=dict(session=session))
        processes.append(p)
        p.start()
    for p in processes: p.join()


def add_products(products_df: pd.DataFrame, *, session) -> None:
    for row in products_df.iterrows():
        session.add(Product(
            product_id=row[0], 
            **row[1],
            image_file=get_hashed_img_filename(row[1]['name'], row[0]) + '.webp'
        ))
        log(f'[add_data_to_db.py] Added product "{row[1]["name"]}"', 'db')
    session.commit()
    

def add_interactions(owners: pd.DataFrame, products_df: pd.DataFrame, *, session) -> None:
    interactions = [
        dict(
            username=urow,
            product_id=prow[0],
            rating=random.randint(1, 5),
            reviews=[random.choice(['Wow', 'It worked', 'Pretty good']) for _ in range(4)],
            in_cart=random.choice([True, False])
        )
        for urow, prow in zip(owners.unique(), products_df.iterrows())
    ]
    
    for row in interactions:
        session.add(Interaction(**row))
        log(f'[add_data_to_db.py] Added interaction "{row["username"]}" <-> {row["product_id"]}', 'db')


def main():
    # Init
    t1 = time.time()
    session = Session()
    # Load & add
    products_df, owners = load_data()
    add_users(owners, session=session)  # Add users first to prevent foreign key issues
    add_products(products_df, session=session)
    add_interactions(owners, products_df, session=session)
    # Finish off
    end_session(session)
    t2 = time.time()
    print(f'Took {(t2-t1):.2f} seconds.')
    
if __name__ == '__main__':
    main()