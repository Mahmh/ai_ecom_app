from dotenv import load_dotenv; load_dotenv()
from langchain_community.llms.ollama import Ollama
from langchain_community.chat_models.ollama import ChatOllama
from langchain_community.embeddings import OllamaEmbeddings
from langchain.schema import SystemMessage
import os, multiprocessing

# LLM
EMBEDDER_LLM_NAME = os.getenv('EMBEDDER_LLM')
CHAT_LLM_NAME = os.getenv('CHAT_LLM')
BASE_URL = os.getenv('BASE_URL')
TEMPERATURE = float(os.environ['TEMPERATURE'])

MAIN_CONFIG = dict(base_url=BASE_URL, num_thread=multiprocessing.cpu_count() - 2, num_gpu=1)
CREATIVE_LLM = Ollama(**MAIN_CONFIG, model=EMBEDDER_LLM_NAME, temperature=1)
EMBEDDER = OllamaEmbeddings(**MAIN_CONFIG, model=EMBEDDER_LLM_NAME, temperature=TEMPERATURE)
CHAT_LLM = ChatOllama(**MAIN_CONFIG, model=CHAT_LLM_NAME, temperature=TEMPERATURE)

CHUNK_SIZE = 500
CHUNK_OVERLAP = 200
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
VECSTORE_PERSIST_DIR=os.path.join(CURRENT_DIR, '../../db/vectorstore')
TOP_K = 9

BASE_SYS_MSG = SystemMessage('You are a helpful assistant that uses EcomGo\'s (our e-commerce company) documents to answer customer questions.')
ERR_RESPONSE = 'Sorry, something went wrong.'

# DB
HOST = os.getenv('POSTGRES_HOST', 'localhost')
PORT = os.getenv('POSTGRES_PORT', '5432')
DB = os.getenv('POSTGRES_DB')
USER = os.getenv('POSTGRES_USER')
PASSWORD = os.getenv('POSTGRES_PASSWORD')

# Misc
ENABLE_LOGGING = os.getenv('ENABLE_LOGGING', 'false')