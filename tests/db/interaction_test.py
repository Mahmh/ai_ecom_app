from src.lib.utils.tests import DBTests, SAMPLE_CRED, SAMPLE_PRODUCT_ID
from src.lib.data.db import InteractionData
from src.lib.utils.db import (
    is_product_in_cart,
    get_all_interactions, 
    rate_product,
    unrate_product,
    get_reviews_of_product, 
    add_product_review,
    remove_product_review,
    update_product_review,
    add_product_to_cart,
    remove_product_from_cart,
    get_most_rated_products
)

class TestInteraction(DBTests):
    def test_get_all_interactions(self):
        interactions = get_all_interactions()
        assert type(interactions) is list and len(interactions) > 0 and type(interactions[0]) is InteractionData, 'Failed to get all interactions'
    
    
    def test_rate_and_unrate_product(self):
        status1 = rate_product(SAMPLE_CRED, SAMPLE_PRODUCT_ID)
        rating1 = get_all_interactions(username=SAMPLE_CRED.username, product_id=SAMPLE_PRODUCT_ID)[0].rating
        status2 = rate_product(SAMPLE_CRED, SAMPLE_PRODUCT_ID)
        rating2 = get_all_interactions(username=SAMPLE_CRED.username, product_id=SAMPLE_PRODUCT_ID)[0].rating
        assert status1 is True and status2 is True, 'Failed to rate product'
        assert rating1 == 1 and rating2 == 1, "Failed to rate product"

        status1 = unrate_product(SAMPLE_CRED, SAMPLE_PRODUCT_ID)
        rating1 = get_all_interactions(username=SAMPLE_CRED.username, product_id=SAMPLE_PRODUCT_ID)[0].rating
        status2 = unrate_product(SAMPLE_CRED, SAMPLE_PRODUCT_ID)
        rating2 = get_all_interactions(username=SAMPLE_CRED.username, product_id=SAMPLE_PRODUCT_ID)[0].rating
        assert status1 is True and status2 is True, 'Failed to rate product'
        assert rating1 == 0 and rating2 == 0, "Failed to unrate product"
    

    def test_add_and_get_reviews_of_product(self):
        reviews_to_add = ['Awesome', 'Thanks']
        status1 = add_product_review(SAMPLE_CRED, SAMPLE_PRODUCT_ID, reviews_to_add[0])
        status2 = add_product_review(SAMPLE_CRED, SAMPLE_PRODUCT_ID, reviews_to_add[1])

        result = get_reviews_of_product(SAMPLE_PRODUCT_ID)
        username = result[0]['username']
        reviews = [review['review'] for review in result]
        sentiments = [review['sentiment'] for review in result]

        assert status1 is True and status2 is True, 'Failed to add reviews'
        assert username == SAMPLE_CRED.username, 'Failed to get the username that made the product review'
        assert len(result) == 2 and len(reviews) == 2, 'Failed to get product reviews'
        assert reviews[0] == reviews_to_add[0] and reviews[1] == reviews_to_add[1], 'Failed to add correct reviews'
        assert sentiments[0] == sentiments[1] == 1, 'Failed to get correct review sentiments'
    

    def test_remove_product_review(self):
        # Add then remove
        add_product_review(SAMPLE_CRED, SAMPLE_PRODUCT_ID, 'Great')
        status = remove_product_review(SAMPLE_CRED, SAMPLE_PRODUCT_ID, 0)
        # Check
        result = get_reviews_of_product(SAMPLE_PRODUCT_ID)
        reviews = [tupl[1] for tupl in result]
        assert status is True and len(reviews) == 0, 'Failed to remove product review'
    

    def test_update_product_review(self):
        # Add then update
        add_product_review(SAMPLE_CRED, SAMPLE_PRODUCT_ID, 'Great')
        new_msg = 'Wow'
        status = update_product_review(SAMPLE_CRED, SAMPLE_PRODUCT_ID, 0, new_msg)
        # Check
        result = get_reviews_of_product(SAMPLE_PRODUCT_ID)
        new_review = result[-1]['review']
        assert status is True and new_review == new_msg, 'Failed to update product review'


    def test_add_product_to_cart(self):
        status = add_product_to_cart(SAMPLE_CRED, SAMPLE_PRODUCT_ID)
        in_cart = is_product_in_cart(SAMPLE_CRED, SAMPLE_PRODUCT_ID)
        assert status is True and in_cart is True, 'Failed to add product to cart'
    

    def test_remove_product_from_cart(self):
        add_product_to_cart(SAMPLE_CRED, SAMPLE_PRODUCT_ID)
        status = remove_product_from_cart(SAMPLE_CRED, SAMPLE_PRODUCT_ID)
        in_cart = is_product_in_cart(SAMPLE_CRED, SAMPLE_PRODUCT_ID)
        assert status is True and in_cart is False, 'Failed to remove product from cart'
    

    def test_get_most_rated_products(self):
        products = get_most_rated_products()
        assert type(products) is list and len(products) == 3, 'Failed to get most rated products'