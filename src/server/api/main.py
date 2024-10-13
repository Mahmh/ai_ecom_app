from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn, os
from src.server.api.routers.model import model_r
from src.server.api.routers.db import account_r, product_r, interaction_r
from src.lib.data.constants import WEB_SERVER_URL, API_SERVER_HOST, API_SERVER_PORT, CURRENT_DIR

# Init
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[WEB_SERVER_URL],
    allow_credentials=True,
    allow_methods=['GET', 'POST', 'PATCH', 'DELETE'],
    allow_headers=['*'],
)
app.mount('/product_images', StaticFiles(directory='../../lib/assets/images/hashed_products'), name='product_images')
app.mount('/user_images', StaticFiles(directory='../../lib/assets/images/users'), name='user_images')

# Routers
for r in (model_r, account_r, product_r, interaction_r):
    app.include_router(r)

# Start
if __name__ == '__main__':
    uvicorn.run(
        'main:app', 
        host=API_SERVER_HOST, 
        port=API_SERVER_PORT,
        reload=True,
        reload_dirs=[os.path.join(CURRENT_DIR, '../')]
    )