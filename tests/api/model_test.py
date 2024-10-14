from src.lib.utils.tests import request, check_status

def test_chatbot_response():
    res = request('chatbot', 'post', prompt='hi', history=[])
    res_data = res.json()
    check_status(res)
    assert type(res_data) is str and not 'sorry' in res_data.lower(), 'Bad response'


def test_review_analyst_inference():
    res = request('review_analyst', 'post', review_text='I didn\'t like it', rating=0)
    res_data = res.json()
    check_status(res)
    assert type(res_data) is float, 'Invalid response type'