from typing import Any, Callable, Tuple, List, Dict
import requests, json, pytest
from src.lib.modules.types.db import Credentials
from src.lib.modules.data.constants import SERVER_URL
from src.lib.modules.utils.db import create_account, create_product, delete_account, delete_product

# Check if API server is running
try: requests.get(SERVER_URL)
except: pytest.exit(reason='Server is not running')

SAMPLE_CRED = Credentials(username='Test User', password='abc')
SAMPLE_PRODUCT_ID = 40
endpoint = lambda x: f'{SERVER_URL}/{x}'
post_req = lambda endpoint_name, **data: requests.post(
    endpoint(endpoint_name), 
    data=json.dumps(data)
)

class Tasks:
    """Used for chaining outputs of independent sequential tasks.

    Example input:
    >>> tasks = Tasks(
    >>>     (lambda: 'hello world',),
    >>>     (lambda x: abs(x), [-4]),
    >>>     (custom_function, [7], dict(id=30))
    >>> )
    >>> outputs = tasks.execute()
    """
    def __init__(self, *func_args_kwargs: Tuple[Tuple[Callable[..., Any], List, Dict]]):
        self.func_args_kwargs = []
        for func_args_kwargs_tuple in func_args_kwargs:
            if len(func_args_kwargs_tuple) == 1:
                self.func_args_kwargs.append((func_args_kwargs_tuple[0], [], {}))
            elif len(func_args_kwargs_tuple) == 2:
                self.func_args_kwargs.append((func_args_kwargs_tuple[0], func_args_kwargs_tuple[1], {}))
            else:
                self.func_args_kwargs.append(func_args_kwargs_tuple)

    def execute(self) -> List[Any]:
        """Executes all tasks & collects & returns their outputs"""
        results = []
        for func, args, kwargs in self.func_args_kwargs:
            if args and kwargs: results.append(func(*args, **kwargs))
            elif kwargs: results.append(func(**kwargs))
            elif args: results.append(func(*args))
            else: results.append(func())
        return results


class DBTests:
    """Base class for performing instructions before and after tests"""
    def setup_method(self, method):
        # Excluding these methods to test account creation itself
        if 'test_create_account' not in repr(method): 
            create_account(SAMPLE_CRED)
            if 'test_create_product' not in repr(method): 
                create_product(SAMPLE_CRED, name='Test Product')
        

    def teardown_method(self, method):
        # Same for that one
        if 'test_delete_account' not in repr(method): 
            delete_account(SAMPLE_CRED)