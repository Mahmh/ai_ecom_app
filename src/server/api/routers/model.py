from fastapi import APIRouter
from src.lib.data.models import ReviewAnalystConfig as config
from src.lib.utils.models import load_checkpoint
from src.lib.data.models import ReviewAnalystInput, ChatbotInput
from src.server.models.chatbot.model import Chatbot
from src.server.models.review_analyst.model import ReviewAnalyst

# Init & Router
review_analyst = load_checkpoint(ReviewAnalyst, config)[0]
chatbot = Chatbot()
model_r = APIRouter()

# Endpoints
@model_r.post('/review_analyst')
async def review_analyst_inference(data: ReviewAnalystInput) -> float:
    return review_analyst([data.review_text, data.rating])

@model_r.post('/chatbot')
async def chatbot_response(data: ChatbotInput) -> str:
    return chatbot(data.prompt, data.conversation)