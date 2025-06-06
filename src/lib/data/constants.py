from dotenv import load_dotenv; load_dotenv()
from langchain_community.llms.ollama import Ollama
from langchain_community.chat_models.ollama import ChatOllama
from langchain_community.embeddings import OllamaEmbeddings
from langchain.schema import SystemMessage
import os

# Net
WEB_SERVER_URL = os.getenv('WEB_SERVER_URL', 'http://localhost:3000')
API_SERVER_HOST = os.getenv('API_SERVER_HOST', '0.0.0.0')
API_SERVER_PORT = int(os.getenv('API_SERVER_PORT', 4000))

# LLM
CREATIVE_LLM_NAME = os.getenv('CREATIVE_LLM', 'llama3')
EMBEDDER_LLM_NAME = os.getenv('EMBEDDER_LLM', 'llama3')
CHAT_LLM_NAME = os.getenv('CHAT_LLM', 'llama3')
CONDITIONAL_LLM_NAME = os.getenv('CONDITIONAL_LLM', 'llama3')
BASE_URL = os.getenv('BASE_URL', 'http://ollama_c:11434')
TEMPERATURE = float(os.getenv('TEMPERATURE', .5))
MAX_CORES = max(os.cpu_count() - 2, 1)

MAIN_CONFIG = dict(base_url=BASE_URL, num_thread=MAX_CORES, num_gpu=1)
CREATIVE_LLM = Ollama(**MAIN_CONFIG, model=CREATIVE_LLM_NAME, temperature=1)
EMBEDDER = OllamaEmbeddings(**MAIN_CONFIG, model=EMBEDDER_LLM_NAME, temperature=TEMPERATURE)
CHAT_LLM = ChatOllama(**MAIN_CONFIG, model=CHAT_LLM_NAME, temperature=TEMPERATURE)
CONDITIONAL_LLM = Ollama(**MAIN_CONFIG, model=CONDITIONAL_LLM_NAME, temperature=0)

CHUNK_SIZE = 500
CHUNK_OVERLAP = 200
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))  # path with respect to this file
VECSTORE_PERSIST_DIR = os.path.join(CURRENT_DIR, '../../db/vectorstore')
TOP_K = 9

BASE_SYS_MSG = SystemMessage('You are a helpful assistant that uses EcomGo\'s (our e-commerce company) documents to answer customer questions.')
ERR_RESPONSE = 'Sorry, something went wrong. Please try again later.'

# DB
PSQL_HOST = os.getenv('POSTGRES_HOST', 'localhost')
PSQL_PORT = os.getenv('POSTGRES_PORT', '5432')
PSQL_DB = os.getenv('POSTGRES_DB')
PSQL_USER = os.getenv('POSTGRES_USER')
PSQL_PASSWORD = os.getenv('POSTGRES_PASSWORD')
ENGINE_URL = f'postgresql+psycopg2://{PSQL_USER}:{PSQL_PASSWORD}@{PSQL_HOST}:{PSQL_PORT}/{PSQL_DB}'

# Recommendation Data Pipeline
PIPELINE_INTERVAL = 240  # 4 minutes in seconds
TRANSFORMED_DATA_PATH = os.path.join(CURRENT_DIR, '../../db/data/transformed_interactions.csv')
TOP_K_RECOMMENDED = 5
EMBEDDER_NAME = 'all-MiniLM-L6-v2'

# Misc
HASHING_ALGORITHM = os.getenv('HASHING_ALGORITHM', 'sha256')
ENABLE_LOGGING = os.getenv('ENABLE_LOGGING', 'false')