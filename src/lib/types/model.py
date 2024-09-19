from pydantic import BaseModel

# AI Models
class ReviewAnalystInput(BaseModel):
    review_text: str
    rating: float