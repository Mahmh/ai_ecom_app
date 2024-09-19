"""Generate synthetic product data using an LLM"""
from textwrap import dedent
import json, sys
from src.lib.modules.data.constants import CREATIVE_LLM

if __name__ == '__main__':
    if len(sys.argv) < 1:
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

        with open('../data/products.json') as file:
            try:
                file_result = json.loads(file.read())
            except json.decoder.JSONDecodeError:
                file_result = []
        
        with open('../data/products.json', 'w') as file:
            file_result.extend([result] if type(result) != list else result)
            file.write(json.dumps(file_result))