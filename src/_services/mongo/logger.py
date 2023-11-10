import json

from fastapi import Depends, Request

from _documents.logs.service import logging_service
from _documents.users.schema import UserList
from _documents.users.service import user_service
from config.settings import *
from utils.logger import logger


class MongoDbLogger():

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'):
            cls.instance = super(MongoDbLogger, cls).__new__(cls)
        elif cls.instance.call_type != kwargs['call_type']:
            cls.instance = super(MongoDbLogger, cls).__new__(cls)
        return cls.instance


    def __init__(self, *args, **kwargs):
        self.call_type = kwargs['call_type']
    

    async def __call__(self, request: Request, user: UserList = Depends(user_service.parse_token_query)):
        return await logging_service.request_create(self.call_type, request, user)


    # async def create(self, request: Request, user: UserList):
    #     body = await request.body()
    #     action = Action(**{
    #         "call_type": self.call_type,
    #         "ip_address": request.headers.get('x-real-ip') or request.client.host,
    #         "user_agent": request.headers.get("user-agent"),
    #         "user_id": str(user.id) if user is not None else None,
    #         "user_email": user.email if user is not None else None,
    #         "method": request.method,
    #         "url": str(request.url),
    #         "path_params": request.path_params,
    #         "query_params": dict(request.query_params),
    #         "body": json.loads(body) if len(body) > 100 else None
    #     })
    #     date = datetime.utcnow().strftime("%Y-%m-%d")
    #     if (
    #         log_info := await self.db_client().find_one({
    #             'date': date
    #         })
    #     ) is not None:
    #         return await self.db_client().update_one(
    #             {'_id': log_info['_id']}, {"$push": {"action": action.dict()}}
    #         )

    #     return await self.db_client().insert_one(
    #         Log(**{"action": [action.dict()], 'date': date}).dict()
    #     )