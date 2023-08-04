from utils.logger import logger
from fastapi import APIRouter, BackgroundTasks, Body, Depends, Request
from fastapi.responses import JSONResponse, RedirectResponse

from .service import *

router = APIRouter()

@router.get("/example", dependencies=[])
async def get_signup(request: Request):
    logger.info('Example webhooks for external API')
    return JSONResponse(status_code=200, content=get_example_result())

