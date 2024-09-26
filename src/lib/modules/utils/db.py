from sqlalchemy import func
from functools import wraps
from sqlalchemy.orm import Session as SessionType
from typing import Callable, Any, List, Union
from src.lib.modules.data.db import Session, UserData, User, ProductData, Product, InteractionData, Interaction
from src.lib.modules.types.db import Credentials, UsernameTaken, WrongCredentials, NotOwner, NonExistent
from src.lib.modules.utils.logger import log, err_log

# Helpers
def exc_handler(func: Callable[..., Any]) -> Callable[..., Any]:
    """Captures DB exceptions and returns their messages to be transmitted from the API server"""
    @wraps(func)
    def wrapper(*args, **kwargs) -> Union[Any, str]:
        try: 
            return func(*args, **kwargs)
        except (UsernameTaken, WrongCredentials, NotOwner, NonExistent) as e:
            err_log(func.__name__, e, 'db')
            return str(e)
    return wrapper


def end_session(session: SessionType, commit: bool = True) -> None:
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


def todict(obj: object) -> dict:
    """Converts the object into a dictionary for either tracking hyperparameters or returning API responses"""
    result = {}
    attrs = [obj for obj in dir(obj) if obj[0] != '_']
    for attr in attrs:
        value = getattr(obj, attr)
        if 'method' not in repr(value):
            result[attr] = value
    return result


def _check_review_index(review_index: int, reviews: List[str]) -> None:
    """Checks if the inputted review index & review list are valid"""
    if len(reviews) == 0:
        raise Exception('Attempted to manipulate an empty review list')
    assert review_index < len(reviews), 'The index of the review you want to remove is out of the range of the review list'

def _list_detach(lst: List[Union[User, Product, Interaction]]) -> List[Union[UserData, ProductData, InteractionData]]:
    """Converts DB entities into a type that doesn't require a session"""
    return [item.detach() for item in lst]



# Tables
### Users ###
def _get_all_users(*, session: SessionType) -> List[User]:
    return session.query(User).all()

def get_all_users() -> List[UserData]:
    """Returns all users"""
    session = Session()
    result = _get_all_users(session=session)
    result = _list_detach(result)
    end_session(session, commit=False)
    return result



def _account_exists(cred: Credentials, *, session: SessionType) -> Union[User, bool]:
    users = _get_all_users(session=session)
    for user in users:
        if cred.username == user.username:
            return user
    return False

def account_exists(cred: Credentials) -> Union[UserData, bool]:
    """Checks if a user account was already created"""
    session = Session()
    result = _account_exists(cred, session=session)
    result = result.detach() if type(result) is User else result
    end_session(session)
    return result



def _log_in_account(cred: Credentials, *, session: SessionType) -> User:
    account = _account_exists(cred, session=session)
    if account:
        if cred.password == account.password: return account
        else: raise WrongCredentials(cred.username, cred.password)
    else:
        raise NonExistent('user', cred.username)

def log_in_account(cred: Credentials) -> UserData:
    """Checks if a user account was already created"""
    session = Session()
    result = _log_in_account(cred, session=session)
    result = result.detach()
    end_session(session)
    return result



def _create_account(cred: Credentials, *, session: SessionType, **user_info) -> bool:
    account = _account_exists(cred, session=session)
    if account:
        raise UsernameTaken(cred.username)
    else:
        session.add(User(username=cred.username, password=cred.password, **user_info))
        log(f'[_create_account] Added user "{cred.username}"', 'db')
        return True

def create_account(cred: Credentials, **user_info) -> bool:
    """Creates an account that is not already created"""
    session = Session()
    result = _create_account(cred, **user_info, session=session)
    end_session(session)
    return result



def _delete_account(cred: Credentials, *, session: SessionType) -> bool:
    account = _log_in_account(cred, session=session)

    for product in session.query(Product).filter_by(owner=account.username).all():
        _delete_product(account, product.product_id, session=session)
    
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



### Products ###
def _get_all_products(*, session: SessionType) -> List[Product]:
    return session.query(Product).all()

def get_all_products() -> List[ProductData]:
    """Returns all products"""
    session = Session()
    result = _get_all_products(session=session)
    result = _list_detach(result)
    end_session(session, commit=False)
    return result



def _get_product_using_id(product_id: int, *, session: SessionType) -> Product:
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



def _is_owner_of_product(cred: Credentials, product_id: int, *, session: SessionType) -> bool:
    product = session.query(Product).filter_by(product_id=product_id).first()

    if product is None:
        raise NonExistent('product', product_id)
    else:
        owner = session.query(User).filter_by(username=product.owner).first()
        return (cred.username == owner.username) and (cred.password == owner.password)

def is_owner_of_product(cred: Credentials, product_id: int) -> bool:
    """Checks if the given credentials are the product's owner's"""
    session = Session()
    result = _is_owner_of_product(cred, product_id, session=session)
    end_session(session)
    return result



def _create_product(cred: Credentials, *, session: SessionType, **product_info) -> bool:
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



def _delete_product(cred: Credentials, product_id: int, *, session: SessionType) -> bool:
    account = _log_in_account(cred, session=session)
    product = _get_product_using_id(product_id, session=session)
    is_owner = _is_owner_of_product(account, product_id, session=session)

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



def _update_product(cred: Credentials, product_id: int, *, session: SessionType, **update_kwargs) -> bool:
    account = _log_in_account(cred, session=session)
    product = _get_product_using_id(product_id, session=session)
    is_owner = _is_owner_of_product(account, product.product_id, session=session)
    if is_owner:
        for attr, new_value in update_kwargs.items():
            setattr(product, attr, new_value)
        return True
    else:
        raise NotOwner(account.username, product.product_id)

def update_product(cred: Credentials, product_id: int, **update_kwargs) -> bool:
    """Updates an existing product only with its owner's correct credentials"""
    session = Session()
    result = _update_product(cred, product_id, **update_kwargs, session=session)
    end_session(session)
    return result



### User-product interactions ###
def _get_all_interactions(*, session: SessionType, **filter_kwargs) -> List[Interaction]:
    return session.query(Interaction).filter_by(**filter_kwargs).all()

def get_all_interactions(**filter_kwargs) -> List[InteractionData]:
    """Returns all user-product interactions (filtering enabled)."""
    session = Session()
    result = _get_all_interactions(**filter_kwargs, session=session)
    result = _list_detach(result)
    end_session(session, commit=False)
    return result



def _update_interaction(cred: Credentials, product_id: int, updater: Callable[[Interaction, dict], None], *, session: SessionType) -> bool:
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

def update_interaction(cred: Credentials, product_id: int, updater: Callable[[Interaction, dict], None]) -> bool:
    """Updates a specified interaction's attributes using a callback function that takes in an interaction along with its attribute-value dictionary and updates it using `setattr()`"""
    session = Session()
    result = _update_interaction(cred, product_id, updater, session=session)
    end_session(session)
    return result



def _rate_product(cred: Credentials, product_id: int, rating: int, *, session: SessionType) -> bool:
    assert 0 <= rating <= 5, 'Rating must be in the range [0, 5]'
    return _update_interaction(cred, product_id, lambda interaction, _: setattr(interaction, 'rating', rating), session=session)

def rate_product(cred: Credentials, product_id: int, rating: int) -> bool:
    """Makes a user (indicated by the given credentials) rate a product"""
    session = Session()
    result = _rate_product(cred, product_id, rating, session=session)
    end_session(session)
    return result



def _get_reviews_of_product(product_id: int, *, session: SessionType) -> List[dict[str, Union[str, List]]]:
    _get_product_using_id(product_id, session=session)
    interactions = _get_all_interactions(session=session, product_id=product_id)
    return [
        {'username': interaction.username, 'reviews': interaction.reviews}
        for interaction in interactions
    ]

def get_reviews_of_product(product_id: int) -> List[dict[str, Union[str, List]]]:
    """Returns all the reviews on a product"""
    session = Session()
    result = _get_reviews_of_product(product_id, session=session)
    end_session(session)
    return result



def _add_product_review(cred: Credentials, product_id: int, review: str, *, session: SessionType) -> bool:
    def _add_review(interaction: Interaction, attrs_values: dict) -> None:
        new = attrs_values['reviews'] + [review] if attrs_values['reviews'] else [review]
        setattr(interaction, 'reviews', new)
    return _update_interaction(cred, product_id, _add_review, session=session)

def add_product_review(cred: Credentials, product_id: int, review: str) -> bool:
    """Appends a user's review on a product to the review list"""
    session = Session()
    result = _add_product_review(cred, product_id, review, session=session)
    end_session(session)
    return result



def _remove_product_review(cred: Credentials, product_id: int, review_index: int, *, session: SessionType) -> bool:
    def _remove_review(interaction: Interaction, attrs_values: dict) -> None:
        reviews = attrs_values['reviews'].copy()
        _check_review_index(review_index, reviews)
        del reviews[review_index]
        setattr(interaction, 'reviews', reviews)
    return _update_interaction(cred, product_id, _remove_review, session=session)

def remove_product_review(cred: Credentials, product_id: int, review_index: int) -> bool:
    """Removes a user's review from a product using its index in the review list"""
    session = Session()
    result = _remove_product_review(cred, product_id, review_index, session=session)
    end_session(session)
    return result



def _update_product_review(cred: Credentials, product_id: int, review_index: int, new_review: str, *, session: SessionType) -> bool:
    def _update_review(interaction: Interaction, attrs_values: dict) -> None:
        reviews = attrs_values['reviews'].copy()
        _check_review_index(review_index, reviews)
        reviews[review_index] = new_review
        setattr(interaction, 'reviews', reviews)
    return _update_interaction(cred, product_id, _update_review, session=session)

def update_product_review(cred: Credentials, product_id: int, review_index: int, new_review: str) -> bool:
    """Updates an existing product review"""
    session = Session()
    result = _update_product_review(cred, product_id, review_index, new_review, session=session)
    end_session(session)
    return result



def _add_product_to_cart(cred: Credentials, product_id: int, *, session: SessionType) -> bool:
    return _update_interaction(cred, product_id, lambda interaction, _: setattr(interaction, 'in_cart', True), session=session)

def add_product_to_cart(cred: Credentials, product_id: int) -> bool:
    """Adds a product to a user's cart"""
    session = Session()
    result = _add_product_to_cart(cred, product_id, session=session)
    end_session(session)
    return result



def _remove_product_from_cart(cred: Credentials, product_id: int, *, session: SessionType) -> bool:
    return _update_interaction(cred, product_id, lambda interaction, _: setattr(interaction, 'in_cart', False), session=session)

def remove_product_from_cart(cred: Credentials, product_id: int) -> bool:
    """Removes a product from a user's cart"""
    session = Session()
    result = _remove_product_from_cart(cred, product_id, session=session)
    end_session(session)
    return result