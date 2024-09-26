from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from src.server.api.routers.model import model_r
from src.server.api.routers.db import account_r, product_r, interaction_r
from src.lib.modules.data.constants import WEB_SERVER_URL, API_SERVER_HOST, API_SERVER_PORT

# Init
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[WEB_SERVER_URL],
    allow_credentials=True,
    allow_methods=['GET', 'POST', 'PUT', 'DELETE'],
    allow_headers=['*'],
)

# Routers
for r in (model_r, account_r, product_r, interaction_r):
    app.include_router(r)

# Start
if __name__ == '__main__':
    uvicorn.run('main:app', host=API_SERVER_HOST, port=API_SERVER_PORT, reload=True)