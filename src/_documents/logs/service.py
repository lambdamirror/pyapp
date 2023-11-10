import json
from datetime import datetime, timedelta
from typing import List
from bson import ObjectId
from fastapi import Request, Depends
from _documents._base.service import BaseService
from _documents._base.schema import ServiceBaseConfig
from _services.mongo.client import MongoDbClient

from .schema import Action, Log
from _documents.users.schema import UserList
from _documents.users.service import user_service
from utils.logger import logger


class LoggingService(BaseService):

    def db_client(self):
        return MongoDbClient().get_docs('logs')

    async def create(self, action: Action):
        date = datetime.utcnow().strftime("%Y-%m-%d")
        if (
            log_info := await self.db_client().find_one({
                'date': date
            })
        ) is not None:
            return await self.db_client().update_one(
                {'_id': log_info['_id']}, {"$push": {"action": action.dict()}}
            )

        return await self.db_client().insert_one(
            Log(**{"action": [action.dict()], 'date': date}).dict()
        )

    async def request_create(self, call_type: str, request: Request, user: UserList, **kwargs):
        if (body := kwargs.get('body')) is None:
            body = await request.body()
            body = json.loads(body) if len(body) < 100 and len(body) > 0 else None
        action = Action(**{
            "call_type": call_type,
            "ip_address": request.headers.get('x-real-ip') or request.client.host,
            "user_agent": request.headers.get("user-agent"),
            "user_id": str(user.id) if user is not None else None,
            "user_email": user.email if user is not None else None,
            "method": request.method,
            "url": str(request.url),
            "path_params": request.path_params,
            "query_params": dict(request.query_params),
            "body": body
        })
        return await self.create(action)
    
    # READ
    async def find(self, query, select=None, sort=None) -> Log:
        return await super().find(query, select, sort)


    async def find_many(self, query, select=None, sort=None, limit=None, skip=None) -> List[Log]:
        return await super().find_many(query, select, sort, limit, skip)
    

    async def cache_lookup(self, item_ids: ObjectId | List[ObjectId]) -> Log | List[Log]:
        return await super().cache_lookup(item_ids)


    async def find_by_date(self, date: str):
        actions = []
        if (
            log := await self.db_client().find_one({'date': date})
        ) is not None:
            actions = [
                json.loads(Action(**x).json()) for x in log['action']
            ]
        return actions
    

    # cron
    async def clean_up(self, days = 90):
        logger.info(f"[CRON] Remove logs that are created more than {days} days ago.")
        logs = await self.find_many({
            "date": {"$lte": (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")}
        })
        if len(logs) > 0:
            await self.delete_many([x.id for x in logs])


logging_service = LoggingService(ServiceBaseConfig(**{
    "document": "product",
    "py_create_class": Log,
    "py_update_class": Log,
    "py_list_class": Log,
    "py_master_class": Log,
    "mongodb_client": MongoDbClient(),
}))

