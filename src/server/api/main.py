from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn, src.server.api.routers.model
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
for module in dir(src.server.api.routers.model):
    if module[-2:] == '_r':
        exec(f'from src.server.api.routers.model import {module}')
        app.include_router(eval(module))

# Start
if __name__ == "__main__":
    uvicorn.run(app, host=API_SERVER_HOST, port=API_SERVER_PORT, reload=True)