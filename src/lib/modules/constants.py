from dotenv import load_dotenv; load_dotenv()
from langchain_community.llms.ollama import Ollama
import os, multiprocessing

# LLM
LLM = os.getenv('LLM')
BASE_URL = os.getenv('BASE_URL')
CREATIVE_LLM = Ollama(
    model=LLM,
    base_url=BASE_URL,
    temperature=1,
    num_thread=multiprocessing.cpu_count() - 2,
    num_gpu=1
)

# DB
HOST = os.getenv('POSTGRES_HOST', 'localhost')
PORT = os.getenv('POSTGRES_PORT', '5432')
DB = os.getenv('POSTGRES_DB')
USER = os.getenv('POSTGRES_USER')
PASSWORD = os.getenv('POSTGRES_PASSWORD')

# Misc
ENABLE_LOGGING = os.getenv('ENABLE_LOGGING', 'false')