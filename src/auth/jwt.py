import os
from datetime import datetime
from datetime import timedelta

import jwt
from fastapi import HTTPException
from _documents.users.schema import UserList

from config.settings import *


# Configuration
if API_SECRET_KEY is None:
    raise BaseException('Missing API_SECRET_KEY env var.')



# Error
CREDENTIALS_EXCEPTION = HTTPException(
    status_code=401,
    detail='Could not validate credentials',
    headers={'WWW-Authenticate': 'Bearer'},
)


# Create token internal function
def create_access_token(*, data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(to_encode, API_SECRET_KEY,
                             algorithm=API_ALGORITHM)
    return encoded_jwt


# Create token for an email
def create_token(user: UserList):
    access_token_expires = timedelta(minutes=API_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={
        'id': str(user.id), 
        'email': user.email,
        'short_name': user.short_name,
        'roles': user.roles,
    }, expires_delta=access_token_expires)
    return access_token


# Decode token for user_id
def decode_user_id(token: str):
    try:
        payload = jwt.decode(token, API_SECRET_KEY, algorithms=[API_ALGORITHM])
        user_id: str = payload.get('id')
        if user_id is None:
            raise CREDENTIALS_EXCEPTION
        return user_id
    except jwt.PyJWTError:
        raise CREDENTIALS_EXCEPTION
