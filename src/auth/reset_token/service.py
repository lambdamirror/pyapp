import json
import re
import time
from datetime import datetime, timedelta

from _documents.users.schema import UserList
from _documents.users.service import user_service
from _services.smtp.schema import EmailSchema
from _services.smtp.service import send_template
from _services.mongo.client import MongoDbClient

from bson import ObjectId
from config.settings import *
from fastapi import Depends, HTTPException
from passlib.hash import pbkdf2_sha256

from .schema import *


async def validate_token(token):
    if (
        reset_token := await MongoDbClient().get_docs('reset_token').find_one({
            "token": token, "status": True, "expired_time": {"$gte": datetime.utcnow()}
        })
    ) is None:
        raise HTTPException(status_code=404, detail=f"Reset token is invalid.")
    return { 'is_valid': True }


async def create_token(key: str, field_type: str, data = None):
    """
    key: user_id or email
    """
    # Check new_email valid
    if field_type == 'email':
        regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        if not re.fullmatch(regex, data['new_email']):
            raise HTTPException(status_code=400, detail=f"Email {data['new_email']} is invalid.")
        if (
            user := await MongoDbClient().get_docs('user').find_one({ 'email': data['new_email'] })
        ) is not None:
            raise HTTPException(status_code=400, detail=f"Email {data['new_email']} is already registered.")

    # Check user not exists
    if (
        user := await MongoDbClient().get_docs('user').find_one(
            { "_id": ObjectId(key) } if ObjectId.is_valid(key) else { 'email': key }
    )
    ) is None:
        raise HTTPException(status_code=400, detail=f"User {key} not found.")

    # Create new reset token
    create_result = await MongoDbClient().get_docs('reset_token').insert_one(
        ResetToken(**{
            "user_id": user['_id'],
            "type": field_type.upper(),
            "data": data['new_email'] if field_type == 'email' else None,
            "status": True,
            "expired_time": datetime.utcnow() + timedelta(minutes=10),
        }).dict()
    )
    # Send email notification for reset token
    if (
        new_token := await MongoDbClient().get_docs('reset_token').find_one({
            "_id": create_result.inserted_id
        })
    ) is not None:
        email = data['new_email'] if field_type == 'email' else user['email']
        await send_template(
                f"reset_{field_type}", 
                EmailSchema(**{
                    "subject": f"Email verification for your account" \
                        if field_type == 'email' else "Password changed for your account",
                    "recipients": [email],
                    "cc": [],
                }),
                **{
                    "email": email,
                    "first_name": user.get('name') or email,
                    "url":  f"{FRONT_END_URL}/{field_type}-reset?token={new_token['token']}",
                    "contact_email": CONTACT_EMAIL,
                }
            )
        return { "message": f"An email has been sent to {email} for verification."}
    raise HTTPException(status_code=500, detail="Cannot create a reset token.")


async def reset_password(token: str, data: ResetPassword):
    # Check token invalid
    if (
        reset_token := await MongoDbClient().get_docs('reset_token').find_one({
            "token": token, "type": "PASSWORD", "status": True, "expired_time": {"$gte": datetime.utcnow()}
        })
    ) is None:
        raise HTTPException(status_code=400, detail=f"Reset token is invalid.")
    # Check user not exists
    if (
        user := await MongoDbClient().get_docs('user').find_one({"_id": reset_token['user_id']})
    ) is None:
        raise HTTPException(status_code=400, detail=f"User {reset_token['user_id']} not found.")
    # Check confirm password matched password
    if data.password != data.confirm_password:
        raise HTTPException(status_code=400, detail="Password confirmed does not match.")
    # Hash password and update to user database
    hashed = pbkdf2_sha256.hash(data.password)
    update_result = await MongoDbClient().get_docs('user').update_one(
        {"_id": user['_id']}, {"$set": { "password": hashed}}
    )
    if update_result.modified_count == 1:
        if (
            updated_user := await user_service.find({"_id": user['_id']})
        ) is not None:
            MongoDbClient().get_docs('reset_token').update_one(
                {"token": token}, {"$set": {"status": False}}
            )
            await user_service.cache_update(updated_user)
            return json.loads(updated_user.json())
    raise HTTPException(status_code=500, detail=f"Cannot set a new password for {reset_token['user_id']}.")


async def reset_email(token: str):
    # Check token invalid
    if (
        reset_token := await MongoDbClient().get_docs('reset_token').find_one({
            "token": token, "type": "EMAIL", "status": True, "expired_time": {"$gte": datetime.utcnow()}
        })
    ) is None:
        raise HTTPException(status_code=400, detail=f"Reset token is invalid.")
    # Check user not exists
    if (
        user := await MongoDbClient().get_docs('user').find_one({"_id": reset_token['user_id']})
    ) is None:
        raise HTTPException(status_code=400, detail=f"User {reset_token['user_id']} not found.")

    # Update result
    update_result = await MongoDbClient().get_docs('user').update_one(
        {"_id": user['_id']}, {"$set": { "email": reset_token['data']}}
    )
    if update_result.modified_count == 1:
        if (
            updated_user := await user_service.find({"_id": user['_id']})
        ) is not None:
            MongoDbClient().get_docs('reset_token').update_one(
                {"token": token}, {"$set": {"status": False}}
            )
            await user_service.cache_update(updated_user)
            return json.loads(updated_user.json())
    raise HTTPException(status_code=500, detail=f"Cannot update the email for {reset_token['user_id']}.")
