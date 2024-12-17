from fastapi import APIRouter
from typing import Dict, List, Union, Any
from src.lib.data.models import ReviewAnalystInput, ChatbotInput
from src.lib.data.db import Credentials, NonExistent
from src.lib.utils.db import todict, account_exists
from src.lib.utils.logger import err_log
from src.server.models.chatbot import Chatbot
from src.server.models.review_analyst import review_analyst, SentimentInt
from src.server.models.recommender import recommend_products

# Init & Router
chatbot = Chatbot()
model_r = APIRouter()

# Endpoints
@model_r.post('/review_analyst')
async def review_analyst_inference(data: ReviewAnalystInput) -> SentimentInt:
    return review_analyst(data.review_text)

@model_r.post('/chatbot')
async def chatbot_response(data: ChatbotInput) -> Dict[str, str]:
    return {
        'sender': 'chatbot',
        'content': chatbot(data.content, data.sender, data.conversation)
    }

@model_r.get('/recommender')
async def recommend(username: str) -> Union[List[Dict], str]:
    if account_exists(Credentials(username=username, password='')):
        return [todict(product) for product in recommend_products(username)]
    else:
        msg = f'Account with username "{username}" does not exist.'
        err_log('recommend', NonExistent('user', username), 'api')
        return msg