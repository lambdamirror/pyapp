from typing import Any, List

from _documents.users.schema import *
from _documents.users.service import user_service
from utils.guard import RoleGuard
from utils.logger import logger
from fastapi import APIRouter, BackgroundTasks, Body, Depends, Request
from fastapi.responses import JSONResponse

from .service import *

router = APIRouter()

ts = TestingService()

@router.get("/verify-token/{email}", dependencies=[
    Depends(RoleGuard([Role.DBA.value])),
])
async def get_test_verify_token(email: str):
    logger.info('[Test] Query verify token for an email on Gateway')
    return JSONResponse(status_code=200, content=await ts.find_token(email))


@router.post("/init/{document}", dependencies=[
    Depends(RoleGuard([Role.DBA.value])),
])
async def get_record_document(document: str):
    logger.info('[Test] Initialize document data.')
    return JSONResponse(status_code=200, content=await ts.initialize(document))

@router.post("/clean-up/{document}", dependencies=[
    Depends(RoleGuard([Role.DBA.value])),
])
async def get_record_document(document: str):
    logger.info('[Test] Clean up document data.')
    return JSONResponse(status_code=200, content=await ts.clean_up(document))
