from fastapi import FastAPI
from pymongo import UpdateOne
from starlette.middleware.sessions import SessionMiddleware

from _documents.users.service import user_service
from auth.google.router import router as auth_google_router
from auth.oauth.router import router as auth_oauth_router
from auth.oauth.service import init_dba
from auth.reset_token.router import router as reset_token_router
from config.settings import *

auth_app = FastAPI()

# Set up the middleware to read the request session
if AUTH_SECRET_KEY is None:
    raise 'Missing SECRET_KEY'
auth_app.add_middleware(SessionMiddleware, secret_key=AUTH_SECRET_KEY)


async def startup_auth():
    await init_dba()

auth_app.include_router(auth_google_router, tags=["google_login"], prefix="/google")
auth_app.include_router(auth_oauth_router, tags=["oauth"], prefix="/oauth")
auth_app.include_router(reset_token_router, tags=["reset_token"], prefix="/reset-token")
