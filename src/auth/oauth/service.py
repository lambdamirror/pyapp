
import json
import uuid
from datetime import datetime, timedelta

from bson import ObjectId
from fastapi import BackgroundTasks, HTTPException, Request

from _documents.logs.service import logging_service
from _documents.users.schema import *
from _documents.users.service import user_service
from _services.smtp.schema import EmailSchema
from _services.smtp.service import send_template
from auth.jwt import create_token
from config.settings import *
from utils.logger import logger


# Helpers
async def init_dba():
    '''
    Register an user and assign DBA role
    '''
    random_password = uuid.uuid4().hex[-10:]
    try:
        result = await register(UserCreate(**{
            'email': DBA_EMAIL,
            'password': random_password,
            'confirm_password': random_password
        }), role=Role.DBA.value, permission=Role.DBA.value, notify=False)
        await user_service.db_client().update_one(
            {"_id": ObjectId(result['id'])}, {"$set": {'status': 'active'}}
        )
        await send_template(
                "dba_initialization", 
                EmailSchema(**{
                    "subject": f"You are the first Database Admin at PyApp",
                    "recipients": [DBA_EMAIL],
                    "cc": [],
                }),
                **{
                    "email": DBA_EMAIL,
                    "username": DBA_EMAIL,
                    "password": random_password,
                    "contact_email": CONTACT_EMAIL,
                }
            )
    except Exception as e:
        if isinstance(e, HTTPException): e = e.detail
        logger.warn(f"[DBA Register Error] {e}")


# CREATE
async def register(data: UserCreate, role: str, background_tasks: BackgroundTasks = None, **kwargs) -> dict:
    '''
    Register for a new user with Password Request
    '''
    # Check user exists
    if (user := await user_service.find({"email": data.email})) is not None:
        raise HTTPException(status_code=400, detail=f"User {data.email} already registered.")
    # Check for valid role
    if role.lower() not in Role.list():
        raise HTTPException(status_code=400, detail=f"{role} is not a valid Role")
    # Check password and confirm_password matched
    if data.password != data.confirm_password:
        raise HTTPException(
            status_code=400, detail="Password confirmed does not match.")
    # Hash password and save to user database
    data.password = user_service.hash_password(data.password)

    try:
        verify_token = uuid.uuid4().hex
        user_data = User(
            **data.dict(), roles=[role],
            verify_token=verify_token
        )
        insert_result = await user_service.db_client().insert_one({
            k: v for k, v in user_data.dict().items() if v is not None
        })

        new_user: UserList = await user_service.find({"_id": insert_result.inserted_id})
        await user_service.cache_update(new_user)

        if kwargs.get("notify") is not False and background_tasks is not None:
            background_tasks.add_task(
                send_template,
                "registration", 
                EmailSchema(**{
                    "subject": f"Verify your email",
                    "recipients": [new_user.email],
                    "cc": [],
                }),
                **{
                    "first_name": new_user.name or new_user.email,
                    "url": f"{FRONT_END_URL}/email-reset?token={verify_token}"
                }
            )
        return json.loads((await user_service.build_record(new_user)).json())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{e}")


async def verify_token(background_tasks: BackgroundTasks, token: str):
    if (
        user := await user_service.find({
            "verify_token": token, "status": 'pending'
        })
    ) is None:
        raise HTTPException(status_code=400, detail=f"Verify token is invalid.")

    await user_service.db_client().update_one(
        {"_id": user.id}, {"$set": {'status': 'active'}}
    )
    updated_user: UserList = await user_service.find({"_id": user.id})
    await user_service.cache_update(updated_user)
    background_tasks.add_task(
        send_template,
        "welcome", 
        EmailSchema(**{
            "subject": f"Welcome to PyApp",
            "recipients": [updated_user.email],
            "cc": [],
        }),
        **{
            "first_name": updated_user.name or updated_user.email,
            "url": FRONT_END_URL
        }
    )
    return json.loads((await user_service.build_record(updated_user)).json())


async def resend_token(background_tasks: BackgroundTasks, email: str):
    if (
        user := await user_service.db_client().find_one({ "email": email, "status": "PENDING" })
    ) is None:
        raise HTTPException(
            status_code=400, detail=f"User email has been either verified or waiting for verification or not found.")
    background_tasks.add_task(
        send_template,
        "registration", 
        EmailSchema(**{
            "subject": f"Verify your email",
            "recipients": [user['email']],
            "cc": [],
        }),
        **{
            "first_name": user['name'] or user['email'],
            "url": f"{FRONT_END_URL}/email-verify?token={user['verify_token']}"
        }
    )
    return {}


# ACTIONS
async def login(request: Request, background_tasks: BackgroundTasks, role: str, email: str, password: str):
    '''
    Login with Password Request
    '''
    # Check user not exist
    if (
        user_data := await user_service.db_client().find_one({"email": email, "status": { "$ne": "deleted"}})
    ) is None:
        raise HTTPException(status_code=401, detail="User not found.")
    user = UserList(**user_data)
    # Check password is None
    if ('password' not in user_data) or (user_data['password'] is None):
        raise HTTPException(
            status_code=401, detail="User or password is incorrect.")
    # Check password hashed matches
    if not user_service.verify_password(password, user_data['password']):
        raise HTTPException(
            status_code=401, detail="User or password is incorrect.")
    if user.status == 'pending':
        raise HTTPException(
            status_code=401, detail="Please check your emails for verification link.")
    if user.status in ['inactive', 'locked']:
        raise HTTPException(
            status_code=401, detail=f"Your account is {user.status.lower()}")
    # Add logs
    background_tasks.add_task(logging_service.request_create, 'oauth', request, user, body={'username': email})
    background_tasks.add_task(user_service.push_login_info, request, user)
    return {'result': True, 'access_token': create_token(role, user)}
    
