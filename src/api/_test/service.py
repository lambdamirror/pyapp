
from fastapi import HTTPException
from _documents.logs.service import logging_service
from _documents.notifications.service import notification_service
from _documents.users.schema import *
from _documents.users.service import user_service


class TestingService():

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(TestingService, cls).__new__(cls)
        return cls.instance
    
    async def find_token(self, email):
        if (user := await user_service.db_client().find_one({'email': email})) is None:
            raise HTTPException(status_code=404, detail=f'User {email} not found.')
        return { 'verify_token': user['verify_token'] }


    # helpers
    async def remove_users(self, user_ids: List[str]):
        order_ids = []
        notification_ids = await notification_service.find_ids(query={"reference_id" : order_ids})
        await user_service.delete_many(user_ids)
        await notification_service.delete_many(notification_ids)
        return
    

    # Initialize
    async def initialize(self, document):
        func = getattr(self, f"{document}_init")
        await func()
        return
    

    # Clean up
    async def clean_up(self, document):
        func = getattr(self, f"{document}_clean_up")
        await func()
        return


    async def user_clean_up(self):
        user_ids = await user_service.find_ids(query={'email': {'$regex': '^user.*phtstudio.com$'}})
        await self.remove_users(user_ids)
        return {}
