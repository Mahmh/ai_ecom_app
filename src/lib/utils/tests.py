import requests, json, pytest
from src.lib.data.db import Credentials
from src.lib.utils.db import create_account, create_product, delete_account

# Check if API server is running
SERVER_URL = 'http://backend_c:8000'
try: requests.get(SERVER_URL)
except: pytest.exit(reason='Server is not running', returncode=1)

SAMPLE_CRED = Credentials(username='Test User', password='abc')
SAMPLE_PRODUCT_ID = 40
endpoint = lambda x: f'{SERVER_URL}/{x}'


def request(endpoint_name: str, req_type: str, **data) -> requests.Response:
    """Sends an API request & returns its response"""
    match req_type.lower():
        case 'post': req_func = requests.post
        case 'delete': req_func = requests.delete
    return req_func(endpoint(endpoint_name), data=json.dumps(data))


def check_status(res: requests.Response):
    """Checks if the response status code is OK"""
    assert res.status_code == 200, 'Status code not OK'


class DBTests:
    """Base class for performing instructions before and after tests"""
    def setup_method(self, method):
        # Excluding these methods to test account creation itself
        test_name = repr(method)
        if 'test_create_account' not in test_name:
            create_account(SAMPLE_CRED)
            if 'test_create_product' not in test_name: 
                create_product(SAMPLE_CRED, name='Test Product')
        

    def teardown_method(self, method):
        # Same for that one
        test_name = repr(method)
        if 'test_delete_account' not in test_name: 
            delete_account(SAMPLE_CRED)