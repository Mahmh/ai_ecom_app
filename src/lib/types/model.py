from pydantic import BaseModel
from typing import List

class ReviewAnalystInput(BaseModel):
    """Model for accepting required input for the Review Analyst"""
    review_text: str
    rating: float


class ChatbotInput(BaseModel):
    """Model for accepting required input for the chatbot"""
    prompt: str
    history: List = []