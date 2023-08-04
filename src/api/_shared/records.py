from typing import Callable, List

from bson import ObjectId
from fastapi import BackgroundTasks, HTTPException, Request


from _documents.users.schema import *
from _documents.users.service import user_service
from api._shared.schema import RecordsConfig
from auth.jwt import CREDENTIALS_EXCEPTION
from auth.oauth.service import register
from config.settings import *
from utils.helper import get_instance


class RecordsAPI():

    def __init__(self, config: RecordsConfig):
        """
        > The `__init__` function is called when the class is instantiated
        
        :param config: ServiceBaseConfig
        :type config: ServiceBaseConfig
        """
        self.config = config


    def get_fns(self): return self.config.allowed_fns


    def get_order_query(self, user: UserList):
        query = self.config.order_query
        if isinstance(query, Callable):
            return query(user.id)
        return query


    # SHARED
    async def export(self, request: Request, user: UserList, document, data: Any):
        if f'export/{document}' not in self.get_fns(): raise CREDENTIALS_EXCEPTION
        


    async def create_record(
        self, request: Request, background_tasks: BackgroundTasks, user: UserList,
        document: str, create_data
    ):
        if f'create/{document}' not in self.get_fns(): raise CREDENTIALS_EXCEPTION
        data = []
        params = request.query_params
        if document in ['user', 'editor_and_qc']:
            role = params.get('role')
            create_data = get_instance(UserCreate, create_data)
            data = await register(create_data, notify=False, role=role, permission=self.config.role)

        return data


    async def update_record(
        self, request: Request, background_tasks: BackgroundTasks, user: UserList,
        document: str, update_data
    ):
        if f'update/{document}' not in self.get_fns(): raise CREDENTIALS_EXCEPTION
        data = {}
        if document in ['user', 'editor_and_qc']:
            update_data = get_instance(UserUpdateAdmin, update_data)
       
        return data


    async def update_many_records(
        self, request: Request, background_tasks: BackgroundTasks, user: UserList,
        document: str, update_data: List[Any]
    ):
        if f'update_many/{document}' not in self.get_fns(): raise CREDENTIALS_EXCEPTION
        data = []
        
        if document in 'user':
            data = [get_instance(UserUpdateAdmin, x) for x in update_data]
       
        return data


    async def update_record_status(
        self, request: Request, background_tasks: BackgroundTasks, 
        user: UserList, document: str, id: Union[str, List[str]], status: str
    ):
        if f'update_status/{document}' not in self.get_fns(): raise CREDENTIALS_EXCEPTION
        data = {}
        if document in ['user', 'editor_and_qc']:
            data = await user_service.update_status(id, status)
        
        return data
    

    async def permanent_delete(self, request: Request, user: UserList, document: str, ids: Union[str, List[str]]):
        if f'delete/{document}' not in self.get_fns(): raise CREDENTIALS_EXCEPTION
        data = {}
        is_single = not isinstance(ids, list)
        if is_single: ids = [ids]

        ### CODE HERE

        return {
            'data': data
        }
    