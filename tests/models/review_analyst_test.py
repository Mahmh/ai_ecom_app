import pytest
from src.server.models.review_analyst import review_analyst

@pytest.mark.parametrize(
    'review_text',
    [
        ['That was great!'],
        ['Wow. I had this product for 3 years and it is still working.'],
        ['Absolutely amazing product. Highly recommended!'],
        ['This exceeded all my expectations. Fantastic!'],
        ['That was fire']
    ]
)
def test_positive_review(review_text: str):
    assert review_analyst(review_text) == 1, 'Failed to detect positive review'


@pytest.mark.parametrize(
    'review_text',
    [
        ['That was bad!'],
        ['omg when i got it it broke immediately bruh'],
        ['It\'s worse than good'],
        ['Terrible experience. Would not recommend.'],
        ['This product stopped working within a day. Horrible.']
    ]
)
def test_negative_review(review_text: str):
    assert review_analyst(review_text) == -1, 'Failed to detect negative review'


@pytest.mark.parametrize(
    'review_text',
    [
        ['It\'s okay, not great but not bad either.'],
        ['The product is fine, nothing special about it.'],
        ['Average quality, does the job.'],
        ['Meh. It\'s just okay.'],
        ['I neither love it nor hate it. It works.']
    ]
)
def test_neutral_review(review_text: str):
    assert review_analyst(review_text) == 0, 'Failed to detect neutral review'