from typing import List
from fastapi import HTTPException

import pytest
from _documents.users.schema import *
from utils.logger import logger
from config.conftest import *


@pytest.mark.asyncio
async def test_user_service(
    user_service: UserService,    
):
    await caching(user_service)


async def caching(user_service: UserService):
    users = await user_service.cache_get_all()
    assert len(users) == 0

    limit = 100
    users = await user_service.fetch(limit=limit)
    assert len(users) == limit

    users = await user_service.cache_get_all()
    assert len(users) == limit

    await user_service.cache_delete([x.id for x in users])
    users = await user_service.cache_get_all()
    assert len(users) == 0
