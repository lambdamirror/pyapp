import json
from typing import Any, List, Union

from bson import ObjectId
from fastapi import HTTPException
from pydantic import BaseModel
from pymongo import UpdateOne

from _documents._base.schema import *
from _documents.users.schema import UserList
from _services.redis.service import RedisClient
from config.settings import MAX_FETCH_LIMIT, MAX_QUERY_LENGTH
from utils.helper import get_instance


class BaseService():

    def __init__(self, config: ServiceBaseConfig):
        """
        > The `__init__` function is called when the class is instantiated
        
        :param config: ServiceBaseConfig
        :type config: ServiceBaseConfig
        """
        self.config = config


    def db_client(self):
        """
        > This function returns a MongoDB client object that can be used to access the database
        :return: The database client.
        """
        return self.config.mongodb_client.get_docs(self.config.document)


    def transform_list(self, item) -> BaseList:
        """
        > If the `py_list_class` is not set, then return the item as is. Otherwise, return the item as an
        instance of the `py_list_class`
        
        :param item: The item to be transformed
        :return: A list of BaseList objects
        """
        try:
            return get_instance(self.config.py_list_class, item)
        except Exception as e:
            raise e


    def transform_master(self, item) -> BaseMaster:
        """
        > The function takes a `BaseMaster` object and returns a `BaseMaster` object
        
        :param item: The item to be transformed
        :return: The instance of the class that is being passed in.
        """
        return get_instance(self.config.py_master_class, item)


    async def build_record(self, data: Union[BaseModel, List[BaseModel]], user: Union[None, UserList] = None) -> Union[BaseModel, List[BaseModel]]:
        """
        It takes a list of data and a user, and returns a list of data
        
        :param data: The data to be piped to the view
        :type data: Union[BaseModel, List[BaseModel]]
        :param user: The user to pipe the data to. If None, it will pipe to all users
        :type user: Union[None, UserList]
        :return: The data is being returned.
        """
        is_single = not isinstance(data, list)
        if is_single: data = [data]
        return data if not is_single else data[0]


    async def validate_create(self, data: Union[BaseCreate, List[BaseCreate]], user = None, **kwargs):
        """
        It validates the data that is passed to the create function
        
        :param data: The data to validate
        :type data: Union[BaseCreate, List[BaseCreate]]
        :param user: The user who is creating the object
        :return: The messages and the data.
        """
        is_single = not isinstance(data, list)
        if is_single: data = [data]
        messages = []
        return messages, (data if not is_single else data[0])


    async def validate_update(self, data: Union[BaseUpdate, List[BaseUpdate]], user = None, **kwargs):
        """
        It takes a list of updates, and returns a list of messages and a list of updates
        
        :param data: The data to validate
        :type data: Union[BaseUpdate, List[BaseUpdate]]
        :param user: The user who is making the request
        :return: A list of messages and the data.
        """
        is_single = not isinstance(data, list)
        if is_single: data = [data]
        messages = []
        return messages, (data if not is_single else data[0])


    # READ
    async def find(self, query, select=None, sort=None) -> BaseList:
        """
        > Finds the first item in the database that matches the query, and returns it as a BaseList
        
        :param query: The query to find the item
        :param select: A list of fields to return. If None, returns all fields
        :param sort: A list of tuples that specify the sort order
        :return: A BaseList object
        """
        if sort is None: sort = []
        if select is not None:
            item = await self.db_client().find_one(query, select, sort=sort)
        else:
            item = await self.db_client().find_one(query, sort=sort)
        if item is not None: return self.transform_list(item)
        return None
       

    async def find_and_pipe(self, query, select=None, sort=[], user: Union[None, UserList] = None):
        """
        It takes a query, a select, a sort, and a user, and returns a JSON object of the first item that
        matches the query, or None if no item matches the query.
        
        :param query: The query to find the item
        :param select: A list of fields to return. If None, all fields are returned
        :param sort: a list of tuples, where the first element is the field to sort by, and the second
        element is the direction (1 for ascending, -1 for descending)
        :param user: The user who is requesting the data
        :type user: Union[None, UserList]
        :return: A JSON object
        """
        if (item := await self.find(query, select, sort)) is not None:
            piped: BaseModel = await self.build_record(item, user)
            return json.loads(piped.json())
        return None
    

    async def find_many(self, query, select=None, sort=None, limit=None, skip=None) -> List[BaseList]:
        """
        It takes a query, and returns a list of BaseList objects
        
        :param query: The query to find the documents
        :param select: A list of fields to include or exclude
        :param sort: A list of (key, direction) pairs specifying the sort order for this query
        :param limit: The maximum number of documents to return
        :param skip: The number of documents to skip
        :return: A list of BaseList objects
        """
        items: List[BaseModel] = []
        cursor = self.db_client().find(query)
        if select is not None: cursor = self.db_client().find(query, select)
        if sort is not None: cursor = cursor.sort(sort)
        if limit is not None: cursor = cursor.limit(limit)
        if skip is not None: cursor = cursor.skip(skip)
        for doc in await cursor.to_list(length=MAX_QUERY_LENGTH):
            items.append(self.transform_list(doc))
        return items
    

    async def find_many_and_pipe(self,query, select=None, sort=None, limit=None, skip=None, user: Union[None, UserList] = None):
        """
        > It takes a query, and returns a list of JSON object, where each dictionary is the result of
        piping the corresponding item in the query to the view
        
        :param query: The query to find the items
        :param select: A list of fields to return. If None, returns all fields
        :param sort: a list of tuples, where each tuple is a field name and a direction (1 or -1)
        :param limit: The maximum number of documents to return
        :param skip: The number of documents to skip before returning
        :param user: The user who is requesting the data
        :type user: Union[None, UserList]
        :return: A list of JSON object
        """
        items = await self.find_many(query, select, sort, limit, skip)
        piped_items: List[BaseModel] = await self.build_record(items, user)
        return [json.loads(x.json()) for x in piped_items]

    
    async def find_aggregate(self, query: List[Any]) -> List[Any]:
        """
        It takes a query, runs it, and returns the results
        
        :param query: The query to be executed
        :type query: List[Any]
        :return: A list of documents.
        """
        results = []
        async for doc in self.db_client().aggregate(query):
            results.append(doc)
        return results
    

    async def find_ids(self, **kwargs) -> List[ObjectId]:
        kwargs['select'] = {'_id': 1}
        return [x.id for x in await self.find_many(**kwargs)]


    async def fetch(self, limit=None, skip=0, **kwargs):
        limit = int(limit) if limit is not None else MAX_FETCH_LIMIT
        ids = await self.find_ids(
            query=kwargs.get('query') or {}, 
            select={'_id': 1}, 
            sort=kwargs.get('sort') or [('created_at', -1)], 
            limit=limit, skip=skip
        )
        items = await self.cache_lookup(ids)
        items = await self.build_record(items)
        page = int(skip / limit) + 1

        return {
            'data': [json.loads(x.json()) for x in items],
            'count': await self.db_client().count_documents(kwargs.get('query') or {}),
            'page': page
        }
    

    # CREATE
    async def create(self, data: BaseCreate, user: UserList = None, **kwargs) -> dict:
        """
        It validates the data, transforms it, inserts it into the database, and then returns the new item
        
        :param data: The data that is being created
        :type data: BaseCreate
        :param user: UserList = None
        :type user: UserList
        :return: The new item is being returned.
        """
        messages, data = await self.validate_create(data, user, **kwargs)
        if len(messages) > 0:
            raise HTTPException(status_code=400, detail='\n '.join(messages))
        data = self.transform_master(data.dict())
        inserted_result = await self.db_client().insert_one(
            {k: v for k, v in data.dict().items() if v is not None}
        )
        new_item = await self.find({
            "_id": inserted_result.inserted_id
        })

        await self.cache_update(new_item)

        return json.loads((await self.build_record(new_item, user)).json())


    async def create_many(self, data: List[BaseCreate], user: UserList = None, **kwargs):
        """
        > It takes a list of objects, validates them, transforms them, inserts them into the database, and
        returns the list of objects
        
        :param data: List[BaseCreate]
        :type data: List[BaseCreate]
        :param user: UserList = None
        :type user: UserList
        :return: A list of dictionaries.
        """
        messages, data = await self.validate_create(data, user, **kwargs)
        if len(messages) > 0:
            raise HTTPException(status_code=400, detail='\n '.join(messages))
        data = [self.transform_master(x.dict()) for x in data]
        inserted_result = await self.db_client().insert_many(
            [{
                k: v for k, v in x.dict().items() if v is not None
            } for x in data]
        )
        items: List[BaseList] = await self.find_many({
            '_id': { '$in': inserted_result.inserted_ids } 
        })

        await self.cache_update(items)

        return [json.loads((await self.build_record(x, user)).json()) for x in items]


    # UPDATE
    async def update(self, data: BaseUpdate, user: UserList = None, **kwargs):
        """
        > It validates the data, updates the database, updates the cache, and returns the updated data
        
        :param data: The data to be updated
        :type data: BaseUpdate
        :param user: UserList = None
        :type user: UserList
        :return: The updated item.
        """
        messages, data = await self.validate_update(data, user, **kwargs)
        if len(messages) > 0:
            raise HTTPException(status_code=400, detail='\n '.join(messages))
        await self.db_client().update_one({
            '_id': data.id
        }, {
            '$set': { 
                **{ k:v for k, v in data.dict().items() if v is not None and not k == 'id' },
                'modified_at': datetime.utcnow()
            }
        }, upsert=True)
        if (
            updated_item := await self.find({"_id": data.id})
        ) is not None:
            await self.cache_update(updated_item)
            return json.loads((await self.build_record(updated_item)).json())
        raise HTTPException(status_code=404, detail=f"Data not found.")


    async def update_many(self, data: List[BaseUpdate], user: UserList = None, **kwargs):
        """
        > It takes a list of `BaseUpdate` objects, validates them, updates the database, and returns a list
        of `BaseList` objects
        
        :param data: List[BaseUpdate] - This is the list of objects that you want to update
        :type data: List[BaseUpdate]
        :param user: UserList = None
        :type user: UserList
        :return: A list of dictionaries
        """
        messages, data = await self.validate_update(data, user, **kwargs)
        if len(messages) > 0:
            raise HTTPException(status_code=400, detail='\n '.join(messages))
        # Update accounts
        await self.db_client().bulk_write([
            UpdateOne({
                '_id': d.id,
            }, {
                '$set': { 
                    **{ k:v for k, v in d.dict().items() if v is not None and not k == 'id' },
                    'modified_at': datetime.utcnow()
                }
            }, upsert=True) for d in data
        ], ordered=False)

        # Find the updated accounts
        items: List[BaseList] = await self.find_many({
            '_id': { '$in': [x.id for x in data] }
        })

        await self.cache_update(items)

        return  [json.loads(x.json()) for x in await self.build_record(items)]


    async def update_status(self, item_id: Union[str, List[str]], status: str):
        """
        > Update the status of a record
        
        :param item_id: The ID of the item to update
        :type item_id: Union[str, List[str]]
        :param status: The status to update the record to
        :type status: str
        :return: The updated items.
        """
        is_single = not isinstance(item_id, list)
        if is_single: item_id = [item_id]
        status = status.upper()
        if status not in self.config.record_status:
            raise HTTPException(status_code=401, detail="Status invalid.")
        # Update the status
        update_result = await self.db_client().update_many(
            {"_id": {"$in": [ObjectId(x) for x in item_id]}}, {"$set": {'status': status}}
        )
        # Check the update results
        if update_result.modified_count > 0:
            if (
                updated_items := await self.find_many({"_id": {"$in": [ObjectId(x) for x in item_id]}})
            ) is not None:
                await self.cache_update(updated_items)
                piped_items = await self.build_record(updated_items)
                if is_single:
                    return json.loads(piped_items[0].json())
                else:
                    return [json.loads(x.json()) for x in piped_items]
        
        raise HTTPException(
            status_code=404, detail=f"Data not found.")
    
    
    # DELETE
    async def delete_many(self, ids: List[str]):
        """
        It deletes the documents with the given ids from the database and then deletes the cache entries for
        those ids
        
        :param ids: List[str]
        :type ids: List[str]
        :return: The number of documents deleted and the ids of the documents deleted.
        """
        result = await self.db_client().delete_many({
            '_id': {'$in': [ObjectId(i) for i in ids]}
        })
        await self.cache_delete(ids)
        return { 'deleted_count': result.deleted_count, "deleted_id": ids}


    # Caching
    async def cache_clear(self):
        await RedisClient().delete_pattern(f'{self.config.document}:*')


    async def cache_get_keys(self, keys) -> List[BaseList]:
        cached_data = await RedisClient().get_keys([f'{self.config.document}:{x}' for x in keys])
        return [self.transform_list(x) for x in cached_data]
    

    async def cache_get_all(self) -> List[BaseList]:
        if (
            cached_data := await RedisClient().get_pattern(f'{self.config.document}:*')
        ) is None:
            return []
        return [self.transform_list(x) for x in cached_data]


    async def cache_update(self, items: Union[List[BaseList], BaseList]):
        """
        It takes a list of `BaseList` objects and updates the cache with them
        
        :param data: The data to be updated
        :type data: Union[List[BaseList], BaseList]
        """
        if not isinstance(items, list): items = [items]
        data = { 
            f'{self.config.document}:{x.id}': json.loads(x.json())
            for x in items 
        }
        if len(data) > 0: await RedisClient().set_keys(data)


    async def cache_lookup(self, item_ids: Union[ObjectId, List[ObjectId]]) -> Union[BaseList, List[BaseList]]:
        """
        It takes a list of item ids, checks if they're in the cache, and if they're not, it fetches them
        from the database and adds them to the cache
        
        :param item_ids: The list of item ids to look up
        :type item_ids: Union[ObjectId, List[ObjectId]]
        :return: A list of BaseList objects
        """
        is_single = not isinstance(item_ids, list)
        if is_single: item_ids = [item_ids]
        item_ids = list(dict.fromkeys([ObjectId(x) for x in item_ids if ObjectId.is_valid(x)]).keys())
        items = await self.cache_get_keys([str(x) for x in item_ids])
        data_to_refetch = [
            x for x in item_ids if next(
                (xx for xx in items if xx.id == x), None
            ) is None
        ]
        if len(data_to_refetch) > 0:
            refetch_items = await self.find_many({'_id': {'$in': data_to_refetch}})
            await self.cache_update(refetch_items)
            items = await self.cache_get_keys([str(x) for x in item_ids])
        if is_single:
            return items[0] if len(items) > 0 else None
        else:
            return items
      

    async def cache_delete(self, ids: List[ObjectId]):
        if len(ids) == 0: return
        await RedisClient().delete_cache(*[
            f'{self.config.document}:{x}' for x in ids
        ])

    