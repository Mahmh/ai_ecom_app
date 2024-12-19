from typing import List
from pydantic import BaseModel

class ReviewAnalystInput(BaseModel):
    """Model for accepting required input for the Review Analyst"""
    review_text: str

class ChatbotInput(BaseModel):
    """Model for accepting user prompt for the chatbot"""
    sender: str
    content: str
    conversation: List = []

class ProductRaterInput(BaseModel):
    ...