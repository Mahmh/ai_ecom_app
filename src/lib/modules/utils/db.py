from sqlalchemy import func
from functools import wraps
from sqlalchemy.orm import Session as SessionType
from typing import Callable, Tuple, Any, List, Union
from src.lib.modules.data.db import Session, UserData, User, ProductData, Product, InteractionData, Interaction
from src.lib.modules.types.db import Credentials, UsernameTaken, WrongCredentials, NotOwner, NonExistent
from src.lib.modules.utils.logger import log, err_log

# Helpers
def base_requester(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator for a function to earn a session and distribute it to upstream functions, acting as a base. In other words, a `base_requester`-decorated function uses a session but does not call any other function that wants to use a session, which makes it the first to earn a session. The idea is to make a scoped session to avoid SQLAlchemy's `DetachedInstanceError` for the whole call stack of private functions. A public function should be the first item in the call stack while private functions are on top of it.

    Any function that uses a session MUST return it:
        - Private functions decorated with `base_requester` MUST return the session.
        - Private functions that call a `base_requester`-decorated function(s) MUST return the session.
        - Private functions that call more than one `base_requester`-decorated function MUST reuse the same session by passing it in other functions.
        - Private functions that use a session AND are NOT `base_requester`-decorated MUST accept an optional `session` keyword parameter if passed.
        - Public functions MUST NOT accept a session NOR return one.
        - Public functions that want to return a DB entity (e.g., `User`, `Product`, `Interaction`) MUST return it in a different type (e.g., `UserData`, `ProductData`, `InteractionData`).
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Tuple[Any, SessionType]:
        try:
            if 'session' in kwargs and kwargs['session'] is not None:
                result = func(*args, **kwargs)
                return result, kwargs['session']
            else:
                if 'session' in kwargs: del kwargs['session']
                session = Session()
                result = func(*args, session=session, **kwargs)
                return result, session
        except Exception as e:
            session.rollback()
            err_log(func.__name__, e, 'db')
            raise e
    return wrapper


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
    """This function is called when there are no upstream functions to distribute the scoped session to"""
    if commit: session.commit()
    session.expire_all()
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
@base_requester
def _get_all_users(*, session: SessionType) -> Tuple[List[User], SessionType]:
    return session.query(User).all()

def get_all_users() -> List[UserData]:
    """Returns all users"""
    result, session = _get_all_users()
    result = _list_detach(result)
    end_session(session, commit=False)
    return result



def _account_exists(cred: Credentials, *, session: Union[SessionType, None] = None) -> Tuple[Union[User, bool], SessionType]:
    users, session = _get_all_users(session=session)
    for user in users:
        if cred.username == user.username:
            return user, session
    return False, session

def account_exists(cred: Credentials) -> Union[UserData, bool]:
    """Checks if a user account was already created"""
    result, session = _account_exists(cred)
    result = result.detach() if type(result) is User else result
    end_session(session)
    return result



def _log_in_account(cred: Credentials, *, session: Union[SessionType, None] = None) -> Tuple[User, SessionType]:
    account, session = _account_exists(cred, session=session)
    if account:
        if cred.password == account.password: return account, session
        else: raise WrongCredentials(cred.username, cred.password)
    else:
        raise NonExistent('user', cred.username)

def log_in_account(cred: Credentials) -> UserData:
    """Checks if a user account was already created"""
    result, session = _log_in_account(cred)
    result = result.detach()
    end_session(session)
    return result



def _create_account(cred: Credentials, *, session: Union[SessionType, None] = None, **user_info) -> Tuple[bool, SessionType]:
    account, session = _account_exists(cred, session=session)
    if account:
        raise UsernameTaken(cred.username)
    else:
        session.add(User(username=cred.username, password=cred.password, **user_info))
        log(f'[_create_account] Added user "{cred.username}"', 'db')
        return True, session

def create_account(cred: Credentials, **user_info) -> bool:
    """Creates an account that is not already created"""
    result, session = _create_account(cred, **user_info)
    end_session(session)
    return result



def _delete_account(cred: Credentials, *, session: Union[SessionType, None] = None) -> Tuple[bool, SessionType]:
    account, session = _log_in_account(cred, session=session)

    for product in session.query(Product).filter_by(owner=account.username).all():
        _delete_product(account, product.product_id, session=session)
    
    for interaction in session.query(Interaction).filter_by(username=account.username).all():
        session.delete(interaction)

    session.delete(account)
    return True, session

def delete_account(cred: Credentials) -> bool:
    """Deletes an existing account and all of its products & interctions"""
    result, session = _delete_account(cred)
    end_session(session)
    return result



### Products ###
@base_requester
def _get_all_products(*, session: SessionType) -> Tuple[List[Product], SessionType]:
    return session.query(Product).all()

def get_all_products() -> List[ProductData]:
    """Returns all products"""
    result, session = _get_all_products()
    result = _list_detach(result)
    end_session(session, commit=False)
    return result



def _get_product_using_id(product_id: int, *, session: Union[SessionType, None] = None) -> Tuple[Product, SessionType]:
    products, session = _get_all_products(session=session)
    for product in products:
        if product_id == product.product_id:
            return product, session
    raise NonExistent('product', product_id)

def get_product_using_id(product_id: int) -> ProductData:
    """Returns a product using its ID if it exists"""
    result, session = _get_product_using_id(product_id)
    result = result.detach()
    end_session(session)
    return result



@base_requester
def _is_owner_of_product(cred: Credentials, product_id: int, *, session: SessionType) -> Tuple[bool, SessionType]:
    product = session.query(Product).filter_by(product_id=product_id).first()

    if product is None:
        raise NonExistent('product', product_id)
    else:
        owner = session.query(User).filter_by(username=product.owner).first()
        return (cred.username == owner.username) and (cred.password == owner.password)

def is_owner_of_product(cred: Credentials, product_id: int) -> bool:
    """Checks if the given credentials are the product's owner's"""
    result, session = _is_owner_of_product(cred, product_id)
    end_session(session)
    return result



def _create_product(cred: Credentials, *, session: Union[SessionType, None] = None, **product_info) -> Tuple[bool, SessionType]:
    account, session = _log_in_account(cred, session=session)
    if account:
        max_id = session.query(func.max(Product.product_id)).scalar()
        assert max_id is not None, 'No data in DB'
        new_id = max_id + 1
        session.add(Product(product_id=new_id, owner=account.username, **product_info))
        return True, session

def create_product(cred: Credentials, **product_info) -> bool:
    """Creates & assigns a product only with its owner's correct credentials"""
    result, session = _create_product(cred, **product_info)
    end_session(session)
    return result



def _delete_product(cred: Credentials, product_id: int, *, session: Union[SessionType, None] = None) -> Tuple[bool, SessionType]:
    account, session = _log_in_account(cred, session=session)
    product, session = _get_product_using_id(product_id, session=session)
    is_owner, session = _is_owner_of_product(account, product_id, session=session)

    if is_owner:
        product_interactions, session = _get_all_interactions(product_id=product_id, session=session)
        for interaction in product_interactions: session.delete(interaction)
        session.delete(product)
        return True, session
    else:
        raise NotOwner(cred.username, product_id)


def delete_product(cred: Credentials, product_id: int) -> bool:
    """Deletes & unassigns a product only with its owner's correct credentials"""
    result, session = _delete_product(cred, product_id)
    end_session(session)
    return result



def _update_product(cred: Credentials, product_id: int, *, session: Union[SessionType, None] = None, **update_kwargs) -> Tuple[bool, SessionType]:
    account, session = _log_in_account(cred, session=session)
    product, session = _get_product_using_id(product_id, session=session)
    is_owner, session = _is_owner_of_product(account, product.product_id, session=session)
    if is_owner:
        for attr, new_value in update_kwargs.items():
            setattr(product, attr, new_value)
        return True, session
    else:
        raise NotOwner(account.username, product.product_id)

def update_product(cred: Credentials, product_id: int, **update_kwargs) -> bool:
    """Updates an existing product only with its owner's correct credentials"""
    result, session = _update_product(cred, product_id, **update_kwargs)
    end_session(session)
    return result



### User-product interactions ###
@base_requester
def _get_all_interactions(*, session: SessionType, **filter_kwargs) -> Tuple[List[Interaction], SessionType]:
    return session.query(Interaction).filter_by(**filter_kwargs).all()

def get_all_interactions(**filter_kwargs) -> List[InteractionData]:
    """Returns all user-product interactions (filtering enabled)."""
    result, session = _get_all_interactions(**filter_kwargs)
    result = _list_detach(result)
    end_session(session, commit=False)
    return result



def _update_interaction(cred: Credentials, product_id: int, updater: Callable[[Interaction, dict], None], *, session: Union[SessionType, None] = None) -> Tuple[bool, SessionType]:
    account, session = _log_in_account(cred, session=session)
    _, session = _get_product_using_id(product_id, session=session)
    interactions, session = _get_all_interactions(username=account.username, product_id=product_id, session=session)

    if not interactions:
        interaction = Interaction(username=account.username, product_id=product_id)
        session.add(interaction)
        session.commit()
        interactions, session = _get_all_interactions(username=account.username, product_id=product_id, session=session)

    interaction = interactions[0]
    attrs_values = {element: getattr(interaction, element) for element in dir(interaction) if element[0] != '_'}
    updater(interaction, attrs_values)
    return True, session

def update_interaction(cred: Credentials, product_id: int, updater: Callable[[Interaction, dict], None]) -> bool:
    """Updates a specified interaction's attributes using a callback function that takes in an interaction along with its attribute-value dictionary and updates it using `setattr()`"""
    result, session = _update_interaction(cred, product_id, updater)
    end_session(session)
    return result



def _rate_product(cred: Credentials, product_id: int, rating: int, *, session: Union[SessionType, None] = None) -> Tuple[bool, SessionType]:
    assert 0 <= rating <= 5, 'Rating must be in the range [0, 5]'
    return _update_interaction(cred, product_id, lambda interaction, _: setattr(interaction, 'rating', rating), session=session)

def rate_product(cred: Credentials, product_id: int, rating: int) -> bool:
    """Makes a user (indicated by the given credentials) rate a product"""
    result, session = _rate_product(cred, product_id, rating)
    end_session(session)
    return result



def _get_reviews_of_product(product_id: int, *, session: Union[SessionType, None] = None) -> Tuple[List[dict[str, Union[str, List]]], SessionType]:
    _, session = _get_product_using_id(product_id, session=session)
    interactions, session = _get_all_interactions(session=session, product_id=product_id)
    return [
        {'username': interaction.username, 'reviews': interaction.reviews}
        for interaction in interactions
    ], session

def get_reviews_of_product(product_id: int) -> List[dict[str, Union[str, List]]]:
    """Returns all the reviews on a product"""
    result, session = _get_reviews_of_product(product_id)
    end_session(session)
    return result



def _add_product_review(cred: Credentials, product_id: int, review: str, *, session: Union[SessionType, None] = None) -> Tuple[bool, SessionType]:
    def _add_review(interaction: Interaction, attrs_values: dict) -> None:
        new = attrs_values['reviews'] + [review] if attrs_values['reviews'] else [review]
        setattr(interaction, 'reviews', new)
    return _update_interaction(cred, product_id, _add_review, session=session)

def add_product_review(cred: Credentials, product_id: int, review: str) -> bool:
    """Appends a user's review on a product to the review list"""
    result, session = _add_product_review(cred, product_id, review)
    end_session(session)
    return result



def _remove_product_review(cred: Credentials, product_id: int, review_index: int, *, session: Union[SessionType, None] = None) -> Tuple[bool, SessionType]:
    def _remove_review(interaction: Interaction, attrs_values: dict) -> None:
        reviews = attrs_values['reviews'].copy()
        _check_review_index(review_index, reviews)
        del reviews[review_index]
        setattr(interaction, 'reviews', reviews)
    return _update_interaction(cred, product_id, _remove_review, session=session)

def remove_product_review(cred: Credentials, product_id: int, review_index: int) -> bool:
    """Removes a user's review from a product using its index in the review list"""
    result, session = _remove_product_review(cred, product_id, review_index)
    end_session(session)
    return result



def _update_product_review(cred: Credentials, product_id: int, review_index: int, new_review: str, *, session: Union[SessionType, None] = None) -> Tuple[bool, SessionType]:
    def _update_review(interaction: Interaction, attrs_values: dict) -> None:
        reviews = attrs_values['reviews'].copy()
        _check_review_index(review_index, reviews)
        reviews[review_index] = new_review
        setattr(interaction, 'reviews', reviews)
    return _update_interaction(cred, product_id, _update_review, session=session)

def update_product_review(cred: Credentials, product_id: int, review_index: int, new_review: str) -> bool:
    """Updates an existing product review"""
    result, session = _update_product_review(cred, product_id, review_index, new_review)
    end_session(session)
    return result



def _add_product_to_cart(cred: Credentials, product_id: int, *, session: Union[SessionType, None] = None) -> Tuple[bool, SessionType]:
    return _update_interaction(cred, product_id, lambda interaction, _: setattr(interaction, 'in_cart', True), session=session)

def add_product_to_cart(cred: Credentials, product_id: int) -> bool:
    """Adds a product to a user's cart"""
    result, session = _add_product_to_cart(cred, product_id)
    end_session(session)
    return result



def _remove_product_from_cart(cred: Credentials, product_id: int, *, session: Union[SessionType, None] = None) -> Tuple[bool, SessionType]:
    return _update_interaction(cred, product_id, lambda interaction, _: setattr(interaction, 'in_cart', False), session=session)

def remove_product_from_cart(cred: Credentials, product_id: int) -> bool:
    """Removes a product from a user's cart"""
    result, session = _remove_product_from_cart(cred, product_id)
    end_session(session)
    return result