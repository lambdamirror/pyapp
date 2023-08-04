
import json
from datetime import datetime
from typing import Dict, List, Union

import aioredis

from config.settings import REDIS_URL
from utils.logger import logger

class RedisClient():
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(RedisClient, cls).__new__(cls)
        return cls.instance
    
    def __init__(self) -> None:
        self.redis = aioredis.from_url(REDIS_URL, decode_responses=True)


    def serialize_values(self, data: str):
        def datetime_parser(dct: dict):
            for k, v in dct.items():
                if isinstance(v, str) and v.endswith('+00:00'):
                    try:
                        dct[k] = datetime.fromisoformat(v)
                    except:
                        pass
            return dct
        return json.loads(data, object_hook=datetime_parser)
    

    async def set_cache(self, data, key: str):
        def serialize_dates(v):
            return v.isoformat() if isinstance(v, datetime) else v
        await self.redis.set(
            key,
            json.dumps(data, default=serialize_dates),
        )
    

    async def get_cache(self, key: str):
        data: str = await self.redis.get(key)
        if data is None: return None
        return self.serialize_values(data)
        

    async def set_keys(self, data: Dict[str, str]):
        def serialize_dates(v):
            return v.isoformat() if isinstance(v, datetime) else v
        await self.redis.mset({ 
            k: json.dumps(v, default=serialize_dates) for k, v in data.items() 
        })


    async def get_keys(self, keys: Union[str, List[str]]):
        is_single = not isinstance(keys, list)
        if is_single:
            data: str = await self.redis.get(keys)
            return self.serialize_values(data)
        else:
            data: List[str] = [x for x in await self.redis.mget(keys)
                               if x is not None]
            return [self.serialize_values(x) for x in data]


    async def get_pattern(self, pattern: str):
        keys = await self.redis.keys(pattern)
        return await self.get_keys(keys)


    async def delete_cache(self, *args):
        await self.redis.delete(*args)

    
    async def delete_pattern(self, pattern):
        async for k in self.redis.scan_iter(pattern):
            await self.redis.delete(k)