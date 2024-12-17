from typing import Literal
from src.lib.data.constants import CHAT_LLM

SentimentInt = Literal[1, 0, -1]

class _ReviewAnalyst:
    def __call__(self, review: str) -> SentimentInt:
        return self.predict(review)

    def predict(self, review: str) -> SentimentInt:
        """Predicts the sentiment of the given review by returning 1 for positive, 0 for neutral, and -1 for negative sentiment."""
        prompt = f'''
        Analyze the sentiment of the following review and ONLY respond with:
        - "positive" if the sentiment is positive,
        - "neutral" if the sentiment is neutral,
        - "negative" if the sentiment is negative.

        Review: {review}
        '''

        # Process the response
        response = CHAT_LLM.invoke(prompt)
        sentiment = response.content.strip().lower()

        # Map the sentiment to the corresponding integer value
        if 'positive' in sentiment: return 1
        elif 'neutral' in sentiment: return 0
        elif 'negative' in sentiment: return -1
        else: return 0

review_analyst = _ReviewAnalyst()