from fastapi import APIRouter
from src.lib.data.models import ReviewAnalystInput, ChatbotInput
from src.server.models.chatbot.model import Chatbot
from src.server.models.review_analyst.model import review_analyst, SentimentInt

# Init & Router
chatbot = Chatbot()
model_r = APIRouter()

# Endpoints
@model_r.post('/review_analyst')
async def review_analyst_inference(data: ReviewAnalystInput) -> SentimentInt:
    return review_analyst(data.review_text)

@model_r.post('/chatbot')
async def chatbot_response(data: ChatbotInput) -> str:
    return chatbot(data.prompt, data.conversation)