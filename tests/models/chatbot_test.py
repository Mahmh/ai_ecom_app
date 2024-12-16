import pytest
from src.server.models.chatbot.model import Chatbot

# Fixtures
@pytest.fixture
def chatbot() -> Chatbot:
    return Chatbot()

# Tests
def test_parse_conversation(chatbot):
    msgs = [{'sender': '', 'content': 'Hi.'}, {'sender': 'chatbot', 'content': 'Hello.'}, {'sender': 'system', 'content': '...'}]
    chatbot._parse_conversation(msgs)
    all_msgs = [msg.content for msg in chatbot.history]
    assert len(chatbot.history) == 4, 'Invalid conversation history'
    assert all(msg['content'] in all_msgs for msg in msgs), 'Could not parse messages'


def test_memory(chatbot):
    conv = [
        {'sender': '', 'content': 'my name is Beraw'}, 
        {'sender': 'chatbot', 'content': "Hello Beraw! Welcome to EcomGo's customer support! It's great to have you on board. I don't see any specific questions or concerns from you yet, so feel free to ask me anything about our products, services, or platform in general. I'm here to help!"}
    ]
    answer = chatbot('what is my name', conv=conv)
    assert len(chatbot.history) == 1, 'Memory was not reset'
    assert 'beraw' in answer.lower(), 'Could not remember past info'


@pytest.mark.parametrize(
    'question, answer',
    [
        ('Does EcomGo sell electronics?', 'yes'),
        ('What is my username?', 'gadgetco')
    ]
)
def test_retrieve_docs(chatbot, question, answer):
    response = chatbot.chat(question, sender='GadgetCo')
    assert len(chatbot.history) == 1, 'Memory was not reset'
    assert answer in response.lower(), 'Answer was not in response'