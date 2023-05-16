from fastapi import BackgroundTasks, HTTPException, Request

from _documents.logs.service import logging_service
from _documents.users.schema import *
from _documents.users.service import user_service
from api._shared.schema import DashboardConfig
from config.settings import *
from utils.helper import parse_date


class DashboardAPI():

    def __init__(self, config: DashboardConfig):
        """
        > The `__init__` function is called when the class is instantiated
        
        :param config: ServiceBaseConfig
        :type config: ServiceBaseConfig
        """
        self.config = config
    

    async def get_dashboard(self, user: UserList, document: str, data: dict = {}):
        if document == 'home': return await self.home(user, data)
        if self.config.allowed_docs is not None:
            if document not in self.config.allowed_docs:
                raise HTTPException(status_code=400, detail='Invalid document')
        func = getattr(self, document)
        results = await func(user, data)
        option_keys = self.config.allowed_options.get(document)
        if option_keys is not None:
            results['options'] = {
                k: v for k, v in results['options'].items() if k in option_keys
            }
        return results
    

    
    async def home(self, user: UserList, data: dict, **kwargs):
        return {'data': {}, 'options': {}}


    # Users
    async def user(self, user: UserList, data: dict = {}):
        results = await user_service.fetch(**data)
        return {
            **results,
            'data': results,
            'options': {
                'user_gender': USER_GENDER,
                'billing_provider': BILLING_PROVIDER,
                'email_topic': EMAIL_TOPICS,
                'roles': Role.list(),
                'storage_region': [x['id'] for x in S3_REGION],
            }
        }
    

    # Logs
    async def logs(self, user: UserList, data: dict = {}):
        return {'data': await logging_service.find_by_date(data.get('date'))}
    