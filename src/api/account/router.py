from typing import Any, List

from fastapi import APIRouter, BackgroundTasks, Body, Depends, Request
from fastapi.responses import JSONResponse

from _documents.users.schema import *
from _documents.users.service import user_service
from _services.mongo.logger import MongoDbLogger
from utils.guard import RoleGuard
from utils.logger import logger

from .service import *

router = APIRouter()


# User
@router.get("/profile", dependencies=[
    Depends(MongoDbLogger(call_type='account'))
])
async def get_profile(
    request: Request, user: UserList = Depends(user_service.parse_token_bearer)
):
    logger.info('Get user profile on Gateway')
    return JSONResponse(status_code=200, content=await get_profile_info(user))


@router.patch("/profile", dependencies=[
    Depends(MongoDbLogger(call_type='account'))
])
async def patch_profile(
    request: Request, user: UserList = Depends(user_service.parse_token_bearer),
    data: UserUpdate = Body(...)
):
    logger.info('Update user profile on Gateway')
    return JSONResponse(status_code=200, content=await update_profile(user, data))


@router.get("/notification", dependencies=[
    Depends(MongoDbLogger(call_type='account'))
])
async def get_user_billing_data(
    request: Request, user: UserList = Depends(user_service.parse_token_bearer), skip: int = 0, limit: int = 10
):
    logger.info('Get user notifications on Gateway')
    return JSONResponse(status_code=200, content=await get_notifications(user, skip, limit))


@router.patch("/notification", dependencies=[
    Depends(MongoDbLogger(call_type='account'))
])
async def patch_user_notification(
    request: Request, mode: str | None, ids: List[str] = Body(...),
    user: UserList = Depends(user_service.parse_token_bearer)
):
    logger.info('Mark notifications as read on Gateway')
    return JSONResponse(status_code=200, content=await mark_read_notifications(user, mode, ids))

