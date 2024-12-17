from sqlalchemy import func, select, desc
from sqlalchemy.orm import Session as _SessionType
from typing import Callable, Any, List, Union, Tuple, Dict
from functools import wraps
from difflib import SequenceMatcher
from hashlib import sha256
import bcrypt, re
from src.lib.utils.logger import log, err_log
from src.server.models.review_analyst import review_analyst, SentimentInt
from src.lib.data.db import (
    Session,
    UserData, User, 
    ProductData, Product, 
    InteractionData, Interaction,
    Credentials, SecuredCredentials, UsernameTaken, WrongCredentials, NotOwner, NonExistent
)

# Helpers
def exc_handler(func: Callable[..., Any]) -> Callable[..., Any]:
    """Captures DB exceptions and returns their messages to be transmitted from the API server"""
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Union[Any, str]:
        try: 
            return await func(*args, **kwargs)
        except (UsernameTaken, WrongCredentials, NotOwner, NonExistent, AssertionError) as e:
            err_log(func.__name__, e, 'api')
            return str(e)
    return wrapper


def end_session(session: _SessionType, commit: bool = True) -> None:
    """Ends a given SQLAlchemy session and handles errors when unsuccessful"""
    try:
        if commit: session.commit()
        session.expire_all()
    except Exception as e:
        session.rollback()
        err_log('end_session', e, 'db')
        raise e
    finally:
        session.close()


def todict(obj: object) -> Union[Dict[str, Any], List[Tuple]]:
    """Converts the object into a dictionary for either tracking hyperparameters or returning API responses"""
    result = {}
    attrs = [obj for obj in dir(obj) if obj[0] != '_']
    for attr in attrs:
        value = getattr(obj, attr)
        if 'method' not in repr(value):
            result[attr] = value
    return result


def get_hashed_img_filename(product_name: str, product_id: int) -> str:
    """Returns the product's unique image filename"""
    product_name = product_name.lower().replace(' ', '-').replace("'", '')
    encoded = f'{product_name}{product_id}'.encode()
    return sha256(encoded).hexdigest()


def _check_review_idx(review_idx: int, reviews: List[str]) -> None:
    """Checks if the inputted review index & review list are valid"""
    if len(reviews) == 0:
        raise Exception('Attempted to manipulate an empty review list')
    assert review_idx < len(reviews), f'The index ({review_idx}) of the review you want to remove is out of the range ({len(reviews)}) of the review list'


def _list_detach(lst: List[Union[User, Product, Interaction]]) -> List[Union[UserData, ProductData, InteractionData]]:
    """Converts DB entities into a type that doesn't require a session"""
    return [item.detach() for item in lst]


def _prep_reviews(review_list: List[Dict[str, Union[str, List]]]) -> List[Dict[str, Union[str, SentimentInt]]]:
    """Converts
    ```
    [
        {'username': 'user1', 'reviews': ['review1', 'review2', 'review3'], 'sentiments': [0, 1, 0]},
        {'username': 'user2', 'reviews': ['review1', 'review2'], 'sentiments': [-1, 0]}
    ]
    ```
    to 
    ```
    [
        {'username': 'user1', 'review': 'review1', 'sentiment': 0},
        {'username': 'user1', 'review': 'review2', 'sentiment': 1},
        {'username': 'user1', 'review': 'review3', 'sentiment': 0},
        {'username': 'user2', 'review': 'review1', 'sentiment': -1},
        {'username': 'user2', 'review': 'review2', 'sentiment': 0}
    ]
    ```
    """
    result = []
    for entry in review_list:
        username, reviews, sentiments  = entry['username'], entry['reviews'], entry['sentiments']
        if reviews: result.extend([
            {'username': username, 'review': reviews[review_idx], 'sentiment': sentiments[review_idx]} 
            for review_idx in range(len(reviews))
        ])
    return result


def sanitize(data: Union[str, Credentials]) -> Union[str, Credentials]:
    """Sanitizes data and credentials"""
    if type(data) is str:
        return re.sub(r'[!\?;\'"]', '', data)
    elif type(data) is Credentials:
        return Credentials(username=sanitize(data.username), password=sanitize(data.password))
    else:
        raise TypeError('`sanitize` function supports only 2 types: `str` & `Credentials`')


def _prep_cred(cred: Credentials) -> SecuredCredentials:
    """Prepares the given credentials to be stored in the DB"""
    cred = sanitize(cred)  # Sanitize
    salt = bcrypt.gensalt()  # Generate a salt
    password_hash = bcrypt.hashpw(cred.password.encode('utf-8'), salt)  # Hash the password with the generated salt
    return SecuredCredentials(username=cred.username, password_hash=password_hash, salt=salt)


def _check_password(input_cred: Credentials, account: Union[User, SecuredCredentials]) -> bool:
    """Checks if a given password matches the stored password in the DB for authentication"""
    hashed_password = bcrypt.hashpw(input_cred.password.encode('utf-8'), account.salt)  # Hash the provided password with the stored salt
    return hashed_password == account.password_hash  # Compare the hashed password with the stored password hash


# Tables
### Users ###
def _get_all_users(*, session: _SessionType, **filter_kwargs) -> List[User]:
    return session.query(User).filter_by(**filter_kwargs).all()

def get_all_users(**filter_kwargs) -> List[UserData]:
    """Returns all users"""
    session = Session()
    result = _get_all_users(**filter_kwargs, session=session)
    result = _list_detach(result)
    end_session(session, commit=False)
    return result



def _account_exists(cred: Credentials, *, session: _SessionType) -> Union[User, bool]:
    users = _get_all_users(session=session)
    for user in users:
        if cred.username == user.username: return user
    return False

def account_exists(cred: Credentials) -> Union[UserData, bool]:
    """Checks if a user account was already created"""
    session = Session()
    result = _account_exists(cred, session=session)
    result = result.detach() if type(result) is User else result
    end_session(session, commit=False)
    return result



def _log_in_account(cred: Credentials, *, session: _SessionType) -> User:
    account = _account_exists(cred, session=session)
    if account:
        if _check_password(cred, account): return account
        else: raise WrongCredentials(cred.username, cred.password)
    else:
        raise NonExistent('user', cred.username)

def log_in_account(cred: Credentials) -> UserData:
    """Checks if a user account was already created"""
    session = Session()
    result = _log_in_account(cred, session=session)
    result = result.detach()
    end_session(session, commit=False)
    return result



def _create_account(cred: Credentials, *, session: _SessionType, **user_info) -> Union[User, bool]:
    account = _account_exists(cred, session=session)
    if account:
        raise UsernameTaken(cred.username)
    else:
        secured_cred = _prep_cred(cred)
        created_account = User(username=secured_cred.username, password_hash=secured_cred.password_hash, salt=secured_cred.salt, **user_info)
        session.add(created_account)
        log(f'[_create_account] Added user "{cred.username}"', 'db')
        return created_account

def create_account(cred: Credentials, **user_info) -> Union[UserData, bool]:
    """Creates an account that is not already created"""
    session = Session()
    result = _create_account(cred, **user_info, session=session)
    result = result.detach() if type(result) is User else result
    end_session(session)
    return result



def _delete_account(cred: Credentials, *, session: _SessionType) -> bool:
    account = _log_in_account(cred, session=session)

    for product in session.query(Product).filter_by(owner=account.username).all():
        _delete_product(cred, product.product_id, session=session)
    
    for interaction in session.query(Interaction).filter_by(username=account.username).all():
        session.delete(interaction)

    session.delete(account)
    return True

def delete_account(cred: Credentials) -> bool:
    """Deletes an existing account and all of its products & interctions"""
    session = Session()
    result = _delete_account(cred, session=session)
    end_session(session)
    return result



def _edit_bio(cred: Credentials, new_bio: str, *, session: _SessionType) -> bool:
    account = _log_in_account(cred, session=session)
    account.bio = new_bio
    return True

def edit_bio(cred: Credentials, new_bio: str) -> bool:
    """Modifies an account's bio"""
    session = Session()
    result = _edit_bio(cred, new_bio, session=session)
    end_session(session)
    return result



def _get_user_info(username: str, *, session: _SessionType) -> Dict[str, Union[str, List[Product]]]:
    if _account_exists(Credentials(username=username, password=''), session=session):
        user = _get_all_users(username=username, session=session)[0]
        products = _get_all_products(owner=username, session=session)
        return {'username': user.username, 'bio': user.bio, 'owned_products': products}
    else:
        raise NonExistent('user', username)

def get_user_info(username: str) -> Dict[str, Union[str, List[ProductData]]]:
    session = Session()
    result = _get_user_info(username, session=session)
    result['owned_products'] = _list_detach(result['owned_products'])
    end_session(session)
    return result



def _search_users(search_query: str, similarity_threshold: int = 0.6, *, session: _SessionType) -> List[User]:
    similarity = lambda username: SequenceMatcher(None, username, search_query).ratio()  # Algorithm for computing similarity scores

    # Compare the name of each user with the `search_query` to compute similarity
    matches = []
    for user in _get_all_users(session=session):
        match_score = similarity(user.username)
        if match_score >= similarity_threshold:
            matches.append((user, match_score))
    
    matches.sort(key=lambda x: x[1], reverse=True)  # Sort matches by score in descending order
    return [match[0] for match in matches]  # Return only the elements, not the scores

def search_users(search_query: str, similarity_threshold: float = 0.6) -> List[UserData]:
    """Returns the most relevant users with respect to the `search_query` by computing their similarity scores and returning the products with scores >= `similarity_threshold`"""
    session = Session()
    result = _search_users(search_query, similarity_threshold, session=session)
    result = _list_detach(result)
    end_session(session)
    return result



### Products ###
def _get_all_products(*, session: _SessionType, **filter_kwargs) -> List[Product]:
    return session.query(Product).filter_by(**filter_kwargs).all()

def get_all_products(**filter_kwargs) -> List[ProductData]:
    """Returns all products"""
    session = Session()
    result = _get_all_products(**filter_kwargs, session=session)
    result = _list_detach(result)
    end_session(session, commit=False)
    return result



def _get_product_using_id(product_id: int, *, session: _SessionType) -> Product:
    products = _get_all_products(session=session)
    for product in products:
        if product_id == product.product_id:
            return product
    raise NonExistent('product', product_id)

def get_product_using_id(product_id: int) -> ProductData:
    """Returns a product using its ID if it exists"""
    session = Session()
    result = _get_product_using_id(product_id, session=session)
    result = result.detach()
    end_session(session)
    return result



def _is_owner_of_product(cred: Credentials, product_id: int, *, session: _SessionType) -> bool:
    product = session.query(Product).filter_by(product_id=product_id).first()

    if product is None:
        raise NonExistent('product', product_id)
    else:
        owner = session.query(User).filter_by(username=product.owner).first()
        return (cred.username == owner.username) and _check_password(cred, owner)

def is_owner_of_product(cred: Credentials, product_id: int) -> bool:
    """Checks if the given credentials are the product's owner's"""
    session = Session()
    result = _is_owner_of_product(cred, product_id, session=session)
    end_session(session)
    return result



def _create_product(cred: Credentials, *, session: _SessionType, **product_info) -> bool:
    account = _log_in_account(cred, session=session)
    if account:
        max_id = session.query(func.max(Product.product_id)).scalar()
        assert max_id is not None, 'No data in DB'
        new_id = max_id + 1
        session.add(Product(product_id=new_id, owner=account.username, **product_info))
        return True

def create_product(cred: Credentials, **product_info) -> bool:
    """Creates & assigns a product only with its owner's correct credentials"""
    session = Session()
    result = _create_product(cred, **product_info, session=session)
    end_session(session)
    return result



def _delete_product(cred: Credentials, product_id: int, *, session: _SessionType) -> bool:
    _log_in_account(cred, session=session)
    product = _get_product_using_id(product_id, session=session)
    is_owner = _is_owner_of_product(cred, product_id, session=session)

    if is_owner:
        product_interactions = _get_all_interactions(product_id=product_id, session=session)
        for interaction in product_interactions: session.delete(interaction)
        session.delete(product)
        return True
    else:
        raise NotOwner(cred.username, product_id)


def delete_product(cred: Credentials, product_id: int) -> bool:
    """Deletes & unassigns a product only with its owner's correct credentials"""
    session = Session()
    result = _delete_product(cred, product_id, session=session)
    end_session(session)
    return result



def _update_product(cred: Credentials, product_id: int, *, session: _SessionType, **update_kwargs) -> bool:
    _log_in_account(cred, session=session)
    product = _get_product_using_id(product_id, session=session)
    is_owner = _is_owner_of_product(cred, product.product_id, session=session)
    if is_owner:
        for attr, new_value in update_kwargs.items():
            setattr(product, attr, new_value)
        return True
    else:
        raise NotOwner(cred.username, product.product_id)

def update_product(cred: Credentials, product_id: int, **update_kwargs) -> bool:
    """Updates an existing product only with its owner's correct credentials"""
    session = Session()
    result = _update_product(cred, product_id, **update_kwargs, session=session)
    end_session(session)
    return result



def _search_products(search_query: str, similarity_threshold: int = 0.6, *, session: _SessionType) -> List[Product]:
    similarity = lambda product_name: SequenceMatcher(None, product_name, search_query).ratio() 

    matches = []
    for product in _get_all_products(session=session):
        match_score = similarity(product.name)
        if match_score >= similarity_threshold:
            matches.append((product, match_score))
    
    matches.sort(key=lambda x: x[1], reverse=True) 
    return [match[0] for match in matches]

def search_products(search_query: str, similarity_threshold: float = 0.6) -> List[ProductData]:
    """Returns the most relevant products with respect to the `search_query` by computing their similarity scores and returning the products with scores >= `similarity_threshold`"""
    session = Session()
    result = _search_products(search_query, similarity_threshold, session=session)
    result = _list_detach(result)
    end_session(session)
    return result



### User-product interactions ###
def _get_all_interactions(*, session: _SessionType, **filter_kwargs) -> List[Interaction]:
    return session.query(Interaction).filter_by(**filter_kwargs).all()

def get_all_interactions(**filter_kwargs) -> List[InteractionData]:
    """Returns all user-product interactions (filtering enabled)."""
    session = Session()
    result = _get_all_interactions(**filter_kwargs, session=session)
    result = _list_detach(result)
    end_session(session, commit=False)
    return result



def _update_interaction(cred: Credentials, product_id: int, updater: Callable[[Interaction, Dict], None], *, session: _SessionType) -> bool:
    account = _log_in_account(cred, session=session)
    _get_product_using_id(product_id, session=session)
    interactions = _get_all_interactions(username=account.username, product_id=product_id, session=session)

    if not interactions:
        interaction = Interaction(username=account.username, product_id=product_id)
        session.add(interaction)
        session.commit()
        interactions = _get_all_interactions(username=account.username, product_id=product_id, session=session)

    interaction = interactions[0]
    attrs_values = {element: getattr(interaction, element) for element in dir(interaction) if element[0] != '_'}
    updater(interaction, attrs_values)
    return True

def update_interaction(cred: Credentials, product_id: int, updater: Callable[[Interaction, Dict], None]) -> bool:
    """Updates a specified interaction's attributes using a callback function that takes in an interaction along with its attribute-value dictionary and updates it using `setattr()`"""
    session = Session()
    result = _update_interaction(cred, product_id, updater, session=session)
    end_session(session)
    return result



def _rate_product(cred: Credentials, product_id: int, *, session: _SessionType) -> bool:
    return _update_interaction(cred, product_id, lambda interaction, _: setattr(interaction, 'rating', 1), session=session)

def rate_product(cred: Credentials, product_id: int) -> bool:
    """Makes a user (indicated by the given credentials) rate a product"""
    session = Session()
    result = _rate_product(cred, product_id, session=session)
    end_session(session)
    return result



def _unrate_product(cred: Credentials, product_id: int, *, session: _SessionType) -> bool:
    return _update_interaction(cred, product_id, lambda interaction, _: setattr(interaction, 'rating', 0), session=session)

def unrate_product(cred: Credentials, product_id: int) -> bool:
    """Removes the rating of a user on a product"""
    session = Session()
    result = _unrate_product(cred, product_id, session=session)
    end_session(session)
    return result



def _get_reviews_of_product(product_id: int, *, session: _SessionType) -> List[Dict[str, Union[str, int]]]:
    _get_product_using_id(product_id, session=session)
    interactions = _get_all_interactions(session=session, product_id=product_id)
    return _prep_reviews([
        {'username': interaction.username, 'reviews': interaction.reviews, 'sentiments': interaction.sentiments}
        for interaction in interactions
    ])

def get_reviews_of_product(product_id: int) -> List[Dict[str, Union[str, int]]]:
    """Returns all the reviews made on a product"""
    session = Session()
    result = _get_reviews_of_product(product_id, session=session)
    end_session(session)
    return result



def _add_product_review(cred: Credentials, product_id: int, review: str, *, session: _SessionType) -> bool:
    def _add_review(interaction: Interaction, attrs_values: Dict) -> None:
        reviews_new = attrs_values['reviews'] + [review] if attrs_values['reviews'] else [review]
        sentiments_new = attrs_values['sentiments'] + [review_analyst(review)] if attrs_values['sentiments'] else [review_analyst(review)]
        setattr(interaction, 'reviews', reviews_new)
        setattr(interaction, 'sentiments', sentiments_new)
    return _update_interaction(cred, product_id, _add_review, session=session)

def add_product_review(cred: Credentials, product_id: int, review: str) -> bool:
    """Appends a user's review on a product to the review list"""
    session = Session()
    result = _add_product_review(cred, product_id, review, session=session)
    end_session(session)
    return result



def _remove_product_review(cred: Credentials, product_id: int, review_idx: int, *, session: _SessionType) -> bool:
    def _remove_review(interaction: Interaction, attrs_values: Dict) -> None:
        reviews, sentiments = attrs_values['reviews'].copy(), attrs_values['sentiments'].copy()
        _check_review_idx(review_idx, reviews)
        del reviews[review_idx]
        del sentiments[review_idx]
        setattr(interaction, 'reviews', reviews)
        setattr(interaction, 'sentiments', sentiments)
    return _update_interaction(cred, product_id, _remove_review, session=session)

def remove_product_review(cred: Credentials, product_id: int, review_idx: int) -> bool:
    """Removes a user's review from a product using its index in the review list"""
    session = Session()
    result = _remove_product_review(cred, product_id, review_idx, session=session)
    end_session(session)
    return result



def _update_product_review(cred: Credentials, product_id: int, review_idx: int, new_review: str, *, session: _SessionType) -> bool:
    def _update_review(interaction: Interaction, attrs_values: Dict) -> None:
        reviews, sentiments = attrs_values['reviews'].copy(), attrs_values['sentiments'].copy()
        _check_review_idx(review_idx, reviews)
        reviews[review_idx] = new_review
        sentiments[review_idx] = review_analyst(new_review)
        setattr(interaction, 'reviews', reviews)
        setattr(interaction, 'sentiments', sentiments)
    return _update_interaction(cred, product_id, _update_review, session=session)

def update_product_review(cred: Credentials, product_id: int, review_idx: int, new_review: str) -> bool:
    """Updates an existing product review"""
    session = Session()
    result = _update_product_review(cred, product_id, review_idx, new_review, session=session)
    end_session(session)
    return result



def _is_product_in_cart(cred: Credentials, product_id: int, *, session: _SessionType) -> bool:
    in_cart = False
    for product in _get_cart(cred, session=session):
        if product.product_id == product_id: in_cart = True
    return in_cart

def is_product_in_cart(cred: Credentials, product_id: int):
    """Checks if a product is in a user's cart"""
    session = Session()
    result = _is_product_in_cart(cred, product_id, session=session)
    end_session(session, commit=False)
    return result



def _add_product_to_cart(cred: Credentials, product_id: int, *, session: _SessionType) -> bool:
    assert not _is_product_in_cart(cred, product_id, session=session), 'Product is already in cart'
    return _update_interaction(cred, product_id, lambda interaction, _: setattr(interaction, 'in_cart', True), session=session)

def add_product_to_cart(cred: Credentials, product_id: int) -> bool:
    """Adds a product to a user's cart"""
    session = Session()
    result = _add_product_to_cart(cred, product_id, session=session)
    end_session(session)
    return result



def _remove_product_from_cart(cred: Credentials, product_id: int, *, session: _SessionType) -> bool:
    assert _is_product_in_cart(cred, product_id, session=session), 'Product is not in cart'
    return _update_interaction(cred, product_id, lambda interaction, _: setattr(interaction, 'in_cart', False), session=session)

def remove_product_from_cart(cred: Credentials, product_id: int) -> bool:
    """Removes a product from a user's cart"""
    session = Session()
    result = _remove_product_from_cart(cred, product_id, session=session)
    end_session(session)
    return result



def _get_raters_of_product(product_id: int, *, session: _SessionType) -> List[str]:
    return [
        interaction.username
        for interaction in session.query(Interaction).filter_by(product_id=product_id).all()
        if interaction.rating == 1
    ]

def get_raters_of_product(product_id: int) -> List[str]:
    """Returns the usernames of the raters of a product"""
    session = Session()
    result = _get_raters_of_product(product_id, session=session)
    end_session(session, commit=False)
    return result



def _get_most_rated_products(k: int = 3, *, session: _SessionType) -> List[Product]:
    stmt = select(Interaction).order_by(desc(Interaction.rating)).limit(k)
    interactions = session.execute(stmt).scalars().all()
    return [
        session.query(Product).filter_by(product_id=interaction.product_id)[0]
        for interaction in interactions
    ]

def get_most_rated_products(k: int = 3) -> List[ProductData]:
    """Returns the top `k` most rated products"""
    session = Session()
    result = _get_most_rated_products(k, session=session)
    result = _list_detach(result)
    end_session(session, commit=False)
    return result



def _get_cart(cred: Credentials, *, session: _SessionType) -> List[Product]:
    if log_in_account(cred):
        interactions = _get_all_interactions(username=cred.username, session=session)
        return [
            _get_product_using_id(interaction.product_id, session=session) 
            for interaction in interactions 
            if interaction.in_cart
        ]

def get_cart(cred: Credentials) -> List[ProductData]:
    """Returns the user's cart"""
    session = Session()
    result = _get_cart(cred, session=session)
    result = _list_detach(result)
    end_session(session, commit=False)
    return result