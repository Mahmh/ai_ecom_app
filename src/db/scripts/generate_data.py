"""Generate synthetic user & product data using an LLM"""
from textwrap import dedent
from typing import List, Dict, Any
import json, sys, time, random, string, multiprocessing as mp, pandas as pd
from src.lib.data.constants import CREATIVE_LLM

PRODUCTS_JSON = '../data/products.json'
ACCOUNTS_JSON = '../data/accounts.json'

def get_file_content(file: Any) -> List[Dict]:
    try: content = json.loads(file.read())
    except: content = []
    return content

def gen_products():
    if len(sys.argv) < 2:
        print('Sorry, you missed a command line argument.')
        print('Usage: python3 generate_data.py <NUMBER_OF_ITERATIONS_IN_GENERATING_DATA>')
        exit()

    # Generating subsequently
    for _ in range(int(sys.argv[1])):
        result = CREATIVE_LLM.invoke(dedent('''
            Please generate synthetic JSON data about products. Please only return 4 JSON objects and nothing else. Each JSON object must contain the following properties:
            name (string), description (string), rating (float in the range [0,5]), price (float), discount (float in the range [0,1]), category (string in ["Electronics", "Clothes", "Accessories", "Furniture"]), owner (string), reviews (empty array).
            NOTE: make sure that each JSON object has a unique product category.
        '''))
        result = json.loads(result.replace('```json', '').replace('```', ''))

        with open(PRODUCTS_JSON, 'w') as file:
            content = get_file_content(file)
            content.extend([result] if type(result) != list else result)
            file.write(json.dumps(content))


def gen_user(owner: str, lock: Any):
    user_data = {
        'username': owner.strip(),
        'password': ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(5)]),
        'bio': CREATIVE_LLM.invoke(f'Write a synthetic bio for a fake account named "{owner}". It must be between 3-6 sentences. Your response must only be the bio and nothing else.')
    }
    with lock:
        with open(ACCOUNTS_JSON, 'r+') as file:
            content = get_file_content(file)
            content.append(user_data)
            file.seek(0)
            file.write(json.dumps(content))
            file.truncate()


def gen_users():
    owners = pd.read_json(PRODUCTS_JSON)['owner'].unique()
    processes = []
    lock = mp.Lock()
    for owner in owners:
        p = mp.Process(target=gen_user, args=(owner, lock))
        processes.append(p)
        p.start()
    for p in processes: p.join()


if __name__ == '__main__':
    t1 = time.time()
    gen_products()
    gen_users()
    t2 = time.time()
    print(f'Took {(t2-t1):.2f} seconds.')