import pytest
from src.lib.modules.utils.tests import DBTests, SAMPLE_CRED, SAMPLE_PRODUCT_ID
from src.lib.modules.types.db import NonExistent, NotOwner
from src.lib.modules.data.db import ProductData
from src.lib.modules.utils.db import get_all_products, get_product_using_id, is_owner_of_product, create_product, delete_product, update_product

class TestProduct(DBTests):
    def test_get_all_products(self):
        products = get_all_products()
        assert type(products) is list and len(products) > 0 and type(products[0]) is ProductData, 'Failed to get all products'
    

    def test_get_product_using_id(self):
        product = get_product_using_id(SAMPLE_PRODUCT_ID)
        assert type(product) is ProductData, 'Failed to get product by its ID'
    

    def test_product_does_not_exist(self):
        with pytest.raises(NonExistent):
            get_product_using_id(100)
    

    def test_is_owner_of_product(self):
        assert is_owner_of_product(SAMPLE_CRED, 40) is True, "Couldn't determine product's real owner"
        assert is_owner_of_product(SAMPLE_CRED, 1) is False, "Couldn't determine that an account is not the owner of a product"
    

    def test_create_product(self):
        # Create
        status = create_product(SAMPLE_CRED, name='Test Product')
        # Check
        try: created = bool(get_product_using_id(SAMPLE_PRODUCT_ID))
        except NonExistent: created = False
        assert status is True and created is True, 'Failed to create product'
    

    def test_delete_product(self):
        # Create
        status = delete_product(SAMPLE_CRED, product_id=SAMPLE_PRODUCT_ID)
        # Check
        try: deleted = not bool(get_product_using_id(SAMPLE_PRODUCT_ID)) 
        except NonExistent: deleted = True
        assert status is True and deleted is True, 'Failed to delete product'
    

    def test_delete_product_without_real_owner(self): 
        # Create
        try: status = delete_product(SAMPLE_CRED, product_id=1)
        except NotOwner: status = False
        # Check
        try: deleted = not bool(get_product_using_id(1)) 
        except NonExistent: deleted = True
        assert status is False and deleted is False, "Deleted a product without using its real owner's credentials"
    

    def test_update_product(self):
        # Update
        update_kwargs = dict(name='Renamed Test Product', description='New desc', price=20.5, discount=2, category='New category')
        status = update_product(SAMPLE_CRED, SAMPLE_PRODUCT_ID, **update_kwargs)
        product = get_product_using_id(SAMPLE_PRODUCT_ID)
        assert status is True, "Failed to update product's properties"
        # Check
        for prop in update_kwargs.keys():
            assert getattr(product, prop) == update_kwargs[prop], f"Failed to update product's {prop}"