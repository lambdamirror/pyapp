
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import List

from bson import ObjectId
from fastapi import BackgroundTasks, Depends, HTTPException, Query, Request
from fastapi.security import OAuth2PasswordBearer
from passlib.hash import pbkdf2_sha256
from pymongo import UpdateMany, UpdateOne

from _documents._base.schema import ServiceBaseConfig
from _documents._base.service import BaseService
from _services.mongo.service import MongoDbClient
from _services.s3.manager import s3_manager
from _services.smtp.schema import EmailSchema
from _services.smtp.service import send_template
from auth.jwt import CREDENTIALS_EXCEPTION, create_token, decode_user_id
from config.settings import *
from utils.logger import logger

from .schema import *

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='./oauth/login')


class UserService(BaseService):
    
    # Helpers
    @staticmethod
    def hash_password(password: str):
        return pbkdf2_sha256.hash(password)


    @staticmethod
    def verify_password(password: str, hash: str):
        return pbkdf2_sha256.verify(password, hash)


    async def build_record(self, data: Union[UserList, List[UserList]], user: Union[None, UserList] = None) -> Union[UserList, List[UserList]]:
        is_single = isinstance(data, UserList)
        if is_single: data = [data]
        results = [
            UserList(**{
                **xx.dict(),
                'avatar_src': {
                    'url': s3_manager.get_client().get_presigned_url(key=f"_avatar/{xx.id}"),
                    'presigned_post': s3_manager.get_client().get_presigned_post(key=f"_avatar/{xx.id}")
                }
            }) for xx in data
        ]
        return results[0] if is_single else results


    async def validate_update(self, data: Union[UserUpdate, List[UserUpdate]], user = None, **kwargs):
        is_single = not isinstance(data, list)
        if is_single: data = [data]
        messages = []
        for x in data:
            user_data = UserUpdate(**x.dict())
            if user_data.email_push_topics is not None:
                user_data.email_push_topics = [x for x in user_data.email_push_topics if x in EMAIL_TOPICS]
        return messages, (data if not is_single else data[0])
           
           
    # QUERY
    async def find(self, query, select=None, sort=None) -> UserList:
        return await super().find(query, select, sort)


    async def find_many(self, query, select=None, sort=None, limit=None, skip=None) -> List[UserList]:
        return await super().find_many(query, select, sort, limit, skip)
    

    async def cache_lookup(self, item_ids: Union[ObjectId, List[ObjectId]]) -> Union[UserList, List[UserList]]:
        return await super().cache_lookup(item_ids)


    # UPDATE
    async def push_login_info(self, request: Request, user: UserList):
        # Push login info to user database
        timestamp = datetime.utcnow()
        login_info = {
            "timestamp": [timestamp],
            "ip_address": request.headers.get('x-real-ip') or request.client.host,
            "user_agent": request.headers.get('user-agent')
        }

        # Send email notification for new Log-in and Push login_history
        if len([
            x for x in user.login_history
            if x.ip_address == login_info['ip_address']
            and x.user_agent == login_info['user_agent']
        ]) == 0:
            self.db_client().update_one(
                {"_id": user.id}, {"$push": {"login_history": login_info}}
            )

            await send_template(
                "login", 
                EmailSchema(**{
                    "subject": f"Successful sign-in from new device",
                    "recipients": [user.email],
                    "cc": [],
                }),
                **{
                    **login_info,
                    "timestamp": timestamp.strftime(FULL_DATE_STR_FORMAT),
                    "first_name": user.name or user.email,
                    "password_reset_url": f"{FRONT_END_URL}/user/account?field=security_and_notifications",
                }
            )
        else:
            self.db_client().update_one(
                {
                    "_id": user.id,
                    "login_history": {
                        "$elemMatch": {
                            "ip_address": login_info['ip_address'],
                            "user_agent": login_info['user_agent']
                        }
                    }
                }, {"$push": {"login_history.$.timestamp": timestamp}}
            )
        return


    async def get_current_user(self, token: str = Depends(oauth2_scheme)):
        '''
        Return the user decoded in the jwt token
        '''
        user_id = decode_user_id(token)
        if (
            user := await self.cache_lookup(ObjectId(user_id))
        ) is None:
            raise CREDENTIALS_EXCEPTION
        if user.status != "ACTIVE": raise CREDENTIALS_EXCEPTION
        return user


    async def get_user_ws(self, token: Union[str, None] = Query(default=None)):
        user_id = decode_user_id(token)
        return await self.cache_lookup(ObjectId(user_id))


user_service = UserService(ServiceBaseConfig(**{
    "document": "user",
    "py_update_class": UserUpdate,
    "py_list_class": UserList,
    "py_master_class": User,
    "mongodb_client": MongoDbClient(),
    "record_status": USER_STATUS
}))