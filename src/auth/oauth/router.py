
from fastapi import APIRouter, BackgroundTasks, Body, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm

from _documents.logs.service import MongoDbLogger
from _documents.users.schema import *
from _documents.users.service import user_service
from utils.guard import RoleGuard
from utils.logger import logger

from .service import *

router = APIRouter()


@router.post("/register/{role}")
async def post_register(request: Request, background_tasks: BackgroundTasks, role: str, data: UserCreate = Body(...)):
    logger.info('[User] Register an user on Gateway')
    return JSONResponse(status_code=200, content=await register(data, role=role, background_tasks=background_tasks))


@router.get("/validate/{role}")
async def post_register(request: Request, role: str, user: UserList = Depends(user_service.get_current_user)):
    logger.info('[User] Validate jwt token on Gateway')
    return JSONResponse(status_code=200, content={})


@router.post("/verify/{role}/{token}")
async def post_verify_token(background_tasks: BackgroundTasks, role: str, token: str):
    logger.info('[User] Verify token and activate user on Gateway')
    return JSONResponse(status_code=200, content=await verify_token(role, token, background_tasks))


@router.get("/verify-token/{role}/{email}")
async def get_verify_token(background_tasks: BackgroundTasks, email: str):
    logger.info('[User] Create a new token to verify user on Gateway')
    return JSONResponse(status_code=200, content=await resend_token(email, background_tasks))


@router.post("/login/{role}")
async def post_auth_login(request: Request, background_tasks: BackgroundTasks, role: str, form: OAuth2PasswordRequestForm = Depends()):
    logger.info('Password Request Login on Gateway')
    return JSONResponse(status_code=200, content=await login(request, background_tasks, role, form.username, form.password))


