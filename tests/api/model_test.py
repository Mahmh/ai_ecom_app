from src.lib.modules.data.constants import NOT_OK_MSG
from src.lib.modules.utils.tests import post_req

def test_chatbot_response() -> None:
    request = post_req('chatbot', prompt='hi', history=[])
    assert request.status_code == 200, NOT_OK_MSG
    assert type(request.json()) is str and not 'sorry' in request.json().lower(), 'Bad response'


def test_review_analyst_inference() -> None:
    request = post_req('review_analyst', review_text='I didn\'t like it', rating=0)
    assert request.status_code == 200, NOT_OK_MSG
    assert type(request.json()) is float, 'Invalid response type'