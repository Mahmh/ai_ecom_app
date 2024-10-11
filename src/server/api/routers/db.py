from fastapi import APIRouter, Query
from typing import Union, List, Tuple, Dict
import json
from src.lib.modules.types.db import Credentials
from src.lib.modules.utils.db import (
    exc_handler,
    todict,
    log_in_account,
    create_account,
    delete_account,
    get_all_products,
    get_product_using_id,
    create_product,
    delete_product,
    update_product,
    search_products,
    rate_product,
    get_reviews_of_product,
    add_product_review,
    remove_product_review,
    update_product_review,
    add_product_to_cart,
    remove_product_from_cart,
    get_most_rated_products
)

# Routers
account_r = APIRouter()
product_r = APIRouter()
interaction_r = APIRouter()

# Endpoints
### Users ###
@account_r.post('/log_in_account')
@exc_handler
def log_in_account_(cred: Credentials) -> Union[dict, str]:
    return todict(log_in_account(cred))


@account_r.post('/create_account')
@exc_handler
def create_account_(cred: Credentials, user_info: str = '{}') -> Union[bool, str]:
    return create_account(cred, **json.loads(user_info))
    

@account_r.delete('/delete_account')
@exc_handler
def delete_account_(cred: Credentials) -> Union[bool, str]:
    return delete_account(cred)


### Products ###
@product_r.get('/get_all_products')
@exc_handler
def get_all_products_() -> Union[List[Dict], str]:
    return [todict(p) for p in get_all_products()]


@product_r.get('/get_product_using_id')
@exc_handler
def get_product_using_id_(product_id: int = Query()) -> Union[Dict, str]:
    return todict(get_product_using_id(product_id))


@product_r.post('/create_product')
@exc_handler
def create_product_(cred: Credentials, product_info: str = '{}') -> Union[bool, str]:
    return create_product(cred, **json.loads(product_info))


@product_r.delete('/delete_product')
@exc_handler
def delete_product_(cred: Credentials) -> Union[bool, str]:
    return delete_product(cred)


@product_r.patch('/update_product')
@exc_handler
def update_product_(cred: Credentials, product_id: int, update_kwargs: str) -> Union[bool, str]:
    return update_product(cred, product_id, **json.loads(update_kwargs))


@product_r.get('/search_products')
@exc_handler
def search_products_(search_query: str = Query(), similarity_threshold: float = Query(0.6)) -> Union[List[Dict], str]:
    return [todict(p) for p in search_products(search_query, similarity_threshold)]



### Interactions ###
@interaction_r.patch('/rate_product')
@exc_handler
def rate_product_(cred: Credentials, product_id: int, rating: int) -> Union[bool, str]:
    return rate_product(cred, product_id, rating)


@interaction_r.get('/get_reviews_of_product')
@exc_handler
def get_reviews_of_product_(product_id: int = Query()) -> Union[List[Tuple[str, str]], str]:
    return get_reviews_of_product(product_id)


@interaction_r.patch('/add_product_review')
@exc_handler
def add_product_review_(cred: Credentials, product_id: int, review: str) -> Union[bool, str]:
    return add_product_review(cred, product_id, review)


@interaction_r.delete('/remove_product_review')
@exc_handler
def remove_product_review_(cred: Credentials, product_id: int, review_index: int) -> Union[bool, str]:
    return remove_product_review(cred, product_id, review_index)


@interaction_r.patch('/update_product_review')
@exc_handler
def update_product_review_(cred: Credentials, product_id: int, review_index: int, new_review: str) -> Union[bool, str]:
    return update_product_review(cred, product_id, review_index, new_review)


@interaction_r.patch('/add_product_to_cart')
@exc_handler
def add_product_to_cart_(cred: Credentials, product_id: int) -> Union[bool, str]:
    return add_product_to_cart(cred, product_id)


@interaction_r.delete('/remove_product_from_cart')
@exc_handler
def remove_product_from_cart_(cred: Credentials, product_id: int) -> Union[bool, str]:
    return remove_product_from_cart(cred, product_id)


@interaction_r.get('/get_most_rated_products')
@exc_handler
def remove_product_from_cart_(k: int = Query(default=3)) -> List[Dict]:
    return [todict(i) for i in get_most_rated_products(k)]