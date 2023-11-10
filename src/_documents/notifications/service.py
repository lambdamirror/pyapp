import json
from datetime import timedelta
from typing import List

from bson import ObjectId
from fastapi import HTTPException

from _documents._base.schema import ServiceBaseConfig
from _documents._base.service import BaseService
from _documents.users.schema import UserList
from config.settings import MAX_QUERY_LENGTH
from _services.mongo.client import MongoDbClient

from utils.logger import logger

from .schema import *


class NotificationService(BaseService):
    
    # READ
    async def find(self, query, select=None, sort=None) -> NotificationList:
        return await super().find(query, select, sort)


    async def find_many(self, query, select=None, sort=None, limit=None, skip=None) -> List[NotificationList]:
        return await super().find_many(query, select, sort, limit, skip)


    async def cache_get_keys(self, keys) -> List[NotificationList]:
        return await super().cache_get_keys(keys)


    async def cache_lookup(self, item_ids: ObjectId | List[ObjectId]) -> NotificationList | List[NotificationList]:
        return await super().cache_lookup(item_ids)


    async def fetch_user(self, user: UserList, skip: int = 0, limit: int = 10) -> dict:
        notifications = [ NotificationList(**x) for x in await self.find_aggregate([
            {'$unwind': '$users'},
            {'$match': {'users.user_id': user.id}},
            {'$sort': { 'users.status': -1, 'timestamp': -1}},
            {'$skip': +skip}, {'$limit': +limit}, 
            {'$addFields': { 'status': '$users.status' } },
            {'$project': {'users': 0}}
        ])]

        counts: List[dict] = await self.find_aggregate([
            {'$unwind': '$users'},
            {'$match': {'users.user_id': user.id}},
            {'$group':  {
                '_id': '$users.status',
                'count': {'$sum': 1}
            }}
        ])
        total_count = sum([x.get('count') for x in counts], 0)
        unread_count = next((x.get('count') for x in counts if x.get('_id') == 'UNREAD'), 0)

        return {
            'items': sorted([json.loads(x.json()) for x in notifications], key=lambda x: -x['timestamp']),
            'total_count': total_count,
            'unread_count': unread_count
        }


    # UPDATE
    async def push_many(self, data: List[NotificationCreate]):
        inserted_result = await self.db_client().insert_many(
            [{
                **Notification(**x.dict()).dict()
            } for x in data]
        )

        notifications = [NotificationList(**x) for x in await self.find_aggregate([
            {'$unwind': '$users'},
            {'$match': {'_id': {'$in': inserted_result.inserted_ids}}},
            {'$addFields': { 'user': '$users.user_id', 'status': '$users.status' } },
            {'$project': {'users': 0}}
        ])]

        return sorted(notifications, key=lambda x: x.timestamp, reverse=True)


    async def mark_as_read(self, user: UserList, mode: str = 'partial', notification_ids: List[str] = []):
        # Update the status
        if mode == 'partial':
            query = { "_id": {'$in': [ObjectId(x) for x in notification_ids]} } 
        elif mode == 'all':
            query = { "users.user_id": user.id }
        else:
            raise HTTPException(status_code=400, detail=f"Mode {mode} not allowed.")
        await self.db_client().update_many(
            query, { "$set": {'users.$[user].status': 'READ'} },
            array_filters=[{ "user.user_id": user.id, 'user.status': 'UNREAD' }],
            upsert=False
        )

        notifications = [NotificationList(**x) for x in await self.find_aggregate([
            {'$unwind': '$users'},
            {'$match': {'_id':  {'$in': [ObjectId(x) for x in notification_ids]}, 'users.user_id': user.id}},
            {'$addFields': { 'status': '$users.status' } },
            {'$project': {'users': 0}}
        ])]

        counts: List[dict] = await self.find_aggregate([
            {'$unwind': '$users'},
            {'$match': {'users.user_id': user.id}},
            {'$group':  {
                '_id': '$users.status',
                'count': {'$sum': 1}
            }}
        ])
        unread_count = next((x.get('count') for x in counts if x.get('_id') == 'UNREAD'), 0)

        return {
            'items': sorted([json.loads(x.json()) for x in notifications], key=lambda x: -x['timestamp']), 
            'unread_count':unread_count
        }


    # cron
    async def clean_up(self, days = 90):
        logger.info(f"[CRON] Remove notifications that are created more than {days} days ago.")
        docs = await self.find_many({
            "created_at": {"$lte": datetime.utcnow() - timedelta(days=days)}
        })
        if len(docs) > 0:
            await self.delete_many([x.id for x in docs])


notification_service = NotificationService(ServiceBaseConfig(**{
    "document": "notification",
    "py_create_class": NotificationCreate,
    "py_update_class": None,
    "py_list_class": NotificationList,
    "py_master_class": Notification,
    "mongodb_client": MongoDbClient(),
}))