from fastapi import APIRouter
from typing import Union, List
import json
from src.lib.modules.types.db import Credentials
from src.lib.modules.utils.db import (
    exc_handler, todict,
    log_in_account, create_account, delete_account,
    get_product_using_id, create_product, delete_product, update_product,
    rate_product, get_reviews_of_product, add_product_review, remove_product_review, update_product_review, add_product_to_cart, remove_product_from_cart
)

# Routers
account_r = APIRouter()
product_r = APIRouter()
interaction_r = APIRouter()

# Endpoints
### Users ###
@account_r.post('/log_in_account')
@exc_handler
def log_in_account_(cred: Credentials) -> Union[bool, str]:
    return log_in_account(cred)


@account_r.post('/create_account')
@exc_handler
def create_account_(cred: Credentials, user_info: str = '{}') -> Union[bool, str]:
    return create_account(cred, **json.loads(user_info))
    

@account_r.delete('/delete_account')
@exc_handler
def delete_account_(cred: Credentials) -> Union[bool, str]:
    return delete_account(cred)


### Products ###
@product_r.get('/get_product_using_id/{product_id}')
@exc_handler
def get_product_using_id_(product_id: int) -> Union[dict, str]:
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


### Interactions ###
@interaction_r.patch('/rate_product')
@exc_handler
def rate_product_(cred: Credentials, product_id: int, rating: int) -> Union[bool, str]:
    return rate_product(cred, product_id, rating)


@interaction_r.get('/get_reviews_of_product/{product_id}')
@exc_handler
def get_reviews_of_product_(product_id: int) -> Union[List[dict[str, Union[str, List]]], str]:
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