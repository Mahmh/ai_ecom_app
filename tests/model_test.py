import pytest
from src.server.models.chatbot import Chatbot

# Fixtures
@pytest.fixture
def chatbot() -> Chatbot:
    return Chatbot()

# Tests
def test_parse_conversation(chatbot):
    msgs = [('human', 'Hi.'), ('ai', 'Hello.'), ('system', '...')]
    chatbot.parse_conversation(msgs)
    all_msgs = ' '.join(msg.content for msg in chatbot.history)
    assert len(chatbot.history) == 4
    assert all(msg[1] in all_msgs for msg in msgs)


def test_memory(chatbot):
    chatbot.parse_conversation([('human', 'My name is Beraw'), ('ai', 'Okay.')])
    answer = chatbot.chat('What is my name?')
    assert len(chatbot.history) == 1 # memory was reset
    assert 'Beraw' in answer


@pytest.mark.parametrize(
    'question, answer',
    [
        ('Does EcomGo offer 24/7 customer support?', 'yes')
    ]
)
def test_retrieve_docs(chatbot, question, answer):
    response = chatbot.chat(question)
    assert len(chatbot.history) == 1
    assert answer in response.lower()