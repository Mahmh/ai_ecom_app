import pytest
from src.lib.modules.utils.tests import DBTests, SAMPLE_CRED
from src.lib.modules.types.db import Credentials, WrongCredentials
from src.lib.modules.data.db import UserData
from src.lib.modules.utils.db import get_all_users, account_exists, log_in_account, create_account, delete_account, edit_bio, get_user_info

class TestUser(DBTests):
    def test_get_all_users(self):
        users = get_all_users()
        assert type(users) is list and len(users) > 0 and type(users[0]) is UserData, 'Failed to get all users'
    

    def test_account_exists(self):
        assert type(account_exists(SAMPLE_CRED)) is UserData, 'Failed to check existing account'
    

    def test_account_does_not_exists(self):
        assert account_exists(Credentials(username='RandomUser123', password='abc')) is False, 'Failed to determine non-existent account'
    

    def test_correct_credentials(self):
        assert type(log_in_account(SAMPLE_CRED)) is UserData, 'Failed to log in account'
    

    def test_wrong_credentials(self):
        with pytest.raises(WrongCredentials):
            log_in_account(Credentials(username=SAMPLE_CRED.username, password='wrongpass'))


    def test_create_account(self):
        status = bool(create_account(SAMPLE_CRED))  # Create
        created = bool(account_exists(SAMPLE_CRED))  # Check
        assert status is True and created is True, 'Failed to create account'
    

    def test_delete_account(self):
        status = delete_account(SAMPLE_CRED)  # Delete
        deleted = not bool(account_exists(SAMPLE_CRED))  # Check
        assert status is True and deleted is True, 'Failed to delete account'
    

    def test_edit_bio(self):
        new_bio = 'New Bio'
        status = edit_bio(SAMPLE_CRED, new_bio)
        assert status is True and log_in_account(SAMPLE_CRED).bio == new_bio, 'Failed to edit account\'s bio'
    

    def test_get_user_info(self):
        username = SAMPLE_CRED.username
        user_info = get_user_info(username)
        assert (user_info['username'] == username) and (user_info['bio'] is None) and (len(user_info['owned_products']) == 1), 'Failed to get user info'