from src.lib.utils.tests import request, check_status

def test_sanitize_and_delete_account():
    username, password = ';abcd?', '!!"a'
    sanitized_username, sanitized_password = 'abcd', 'a'
    res1 = request('create_account', 'post', username=username, password=password)
    res1_data = res1.json()
    check_status(res1)
    assert res1_data['username'] == sanitized_username and res1_data['bio'] is None, 'Failed to create account'

    res2 = request('delete_account', 'delete', username=sanitized_username, password=sanitized_password)
    res2_data = res2.json()
    assert res2_data is True, 'Failed to create account'