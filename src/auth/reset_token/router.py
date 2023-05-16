from fastapi import APIRouter, Body, status
from fastapi.responses import JSONResponse
from utils.logger import logger
from .schema import ResetPassword
from .service import *

router = APIRouter()


@router.get("/validate/{token}")
async def get_validate_token(token: str):
    logger.info('Validate token on Gateway')
    return JSONResponse(status_code=status.HTTP_200_OK, content=await validate_token(token))


@router.post("/password/{email}")
async def post_password(email: str, data = Body(...)):
    logger.info('Create a new token to reset password on Gateway')
    return JSONResponse(status_code=status.HTTP_200_OK, content=await create_token(email, field_type='password', data=data))


@router.post("/verify/password/{token}")
async def post_verify_password(token: str, data: ResetPassword):
    logger.info('Verify token and reset password on Gateway')
    return JSONResponse(status_code=status.HTTP_200_OK, content=await reset_password(token, data))


@router.post("/email/{id}")
async def post_email(id: str, data = Body(...)):
    logger.info('Create a new token to reset email on Gateway')
    return JSONResponse(status_code=status.HTTP_200_OK, content=await create_token(id, field_type='email', data=data))


@router.post("/verify/email/{token}")
async def post_verify_email(token: str):
    logger.info('Verify token and reset email on Gateway')
    return JSONResponse(status_code=status.HTTP_200_OK, content=await reset_email(token))