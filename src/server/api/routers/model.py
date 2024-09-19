from fastapi import APIRouter
from src.lib.modules.data.model import model_config
from src.lib.modules.utils.model import load_checkpoint
from src.lib.modules.data.constants import EMBEDDER
from src.lib.types.model import ReviewAnalystInput, ChatbotInput
from src.server.models.chatbot.model import Chatbot

# Init
review_analyst, _ = load_checkpoint(model_config.review_analyst())
chatbot = Chatbot()

# Routers
review_analyst_inference_r = APIRouter()
chatbot_response_r = APIRouter()

# Endpoints
@review_analyst_inference_r.post('/review_analyst')
def review_analyst_inference(data: ReviewAnalystInput):
    review_text, rating = data.review_text, data.rating
    pred = review_analyst([[*EMBEDDER.embed_query(review_text), rating]])
    return pred.tolist()[0][0]

@chatbot_response_r.post('/chatbot')
def chatbot_response(data: ChatbotInput):
    prompt, history = data.prompt, data.history
    chatbot.parse_conversation(history)
    response = chatbot.chat(prompt)
    return response