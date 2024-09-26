from fastapi import APIRouter
from src.lib.modules.data.model import model_config
from src.lib.modules.utils.model import load_checkpoint
from src.lib.modules.data.constants import EMBEDDER
from src.lib.modules.types.model import ReviewAnalystInput, ChatbotInput
from src.server.models.chatbot.model import Chatbot

# Init & Router
review_analyst, _ = load_checkpoint(model_config.review_analyst())
chatbot = Chatbot()
model_r = APIRouter()

# Endpoints
@model_r.post('/review_analyst')
async def review_analyst_inference(data: ReviewAnalystInput):
    review_text, rating = data.review_text, data.rating
    pred = review_analyst([[*EMBEDDER.embed_query(review_text), rating]])
    return pred.tolist()[0][0]

@model_r.post('/chatbot')
async def chatbot_response(data: ChatbotInput):
    prompt, history = data.prompt, data.history
    chatbot.parse_conversation(history)
    response = chatbot.chat(prompt)
    return response