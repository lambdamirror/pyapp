from typing import List

from bson import ObjectId

from _documents._base.schema import ServiceBaseConfig
from _documents._base.service import BaseService
from _documents.settings.schema import *
from _services.mongo.client import MongoDbClient
from _documents._base.schema import List, SearchKeyword

class SettingService(BaseService):

    # Vaidators
    async def validate_category(self, values: List[str]):
        valid_values = await setting_service.get('product_category')
        if any((x.lower() not in valid_values for x in values if x is not None)):
            raise ValueError('Invalid category')
        return 

    async def validate_currency(self, values: List[str]):
        ex_rates = await self.search(
            keywords=[SearchKeyword(field='group', key='exchange_rate')]
        )
        valid_values = {xx for x in ex_rates for xx in [x.key[:3], x.key[3:]]}
        if any((x not in valid_values for x in values if x is not None)):
            raise ValueError('Invalid currency')
        return 
    
    async def validate_create(self, data: SettingCreate | List[SettingCreate], user=None, **kwargs):
        is_single = not isinstance(data, list)
        if is_single: data = [data]
        messages = []
        if (
            exist := await self.find({'name': { '$in': [x.name for x in data] }})
        ) is not None:
            messages.append('Setting variable(s) already exists.')
        return messages, (data if not is_single else data[0])
    
    async def validate_update(self, data: SettingUpdate | List[SettingUpdate], user=None, **kwargs):
        is_single = not isinstance(data, list)
        if is_single: data = [data]
        messages = []
        if (exist := await self.find({
            '$or': [ {'_id': {'$ne': x.id }, 'name': x.name } for x in data ]
        })) is not None:
            messages.append('Variable(s) already exists.')
        return messages, (data if not is_single else data[0])
    
    # READ
    async def find(self, query, select=None, sort=None) -> SettingList:
        return await super().find(query, select, sort)


    async def find_many(self, query, select=None, sort=None, limit=None, skip=None) -> List[SettingList]:
        return await super().find_many(query, select, sort, limit, skip)


    async def cache_lookup(self, item_ids: ObjectId | List[ObjectId]) -> SettingList | List[SettingList]:
        return await super().cache_lookup(item_ids)
    
    
    async def search(self, keywords: List[SearchKeyword], skip=0) -> List[SettingList]:
        return await super().search(keywords, skip)


    async def get(self, key: str, field = 'key'):
        if (doc := await self.find({field: key}, {'_id': 1})) is None:
            return None
        if (doc := await self.cache_lookup(doc.id)) is None:
            return None
        return doc.value if isinstance(doc, SettingList) else [x.value for x in doc]


setting_service = SettingService(ServiceBaseConfig(**{
    "document": "settings",
    "py_create_class": SettingCreate,
    "py_update_class": SettingUpdate,
    "py_list_class": SettingList,
    "py_master_class": Setting,
    "mongodb_client": MongoDbClient(),
}))