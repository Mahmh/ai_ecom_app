from src.lib.utils.tests import request, check_status

def test_chatbot_response():
    res = request('chatbot', 'post', content='hi', sender='', conversation=[])
    res_data = res.json()
    check_status(res)
    assert (res_data['sender'] == 'chatbot') and (not 'sorry' in res_data['content'].lower()), 'Bad response'

def test_review_analyst_inference():
    res = request('review_analyst', 'post', review_text='I didn\'t like it')
    res_data = res.json()
    check_status(res)
    assert type(res_data) is int and res_data == -1, 'Invalid response type'