import requests, json, pytest
from src.lib.modules.data.constants import SERVER_URL

# Check if API server is running
try: requests.get(SERVER_URL)
except: pytest.exit(reason='Server is not running')

# Utilities
NOT_OK_MSG = "Status code not OK"

endpoint = lambda x: f'{SERVER_URL}/{x}'
post_req = lambda endpoint_name, **data: requests.post(
    endpoint(endpoint_name), 
    data=json.dumps(dict(data))
)