
from typing import List
from fastapi import HTTPException

import pytest
from _documents.users.schema import Role, UserList
from _documents.users.service import UserService
from config.settings import CONTACT_EMAIL
from utils.logger import logger
from config.conftest import *
from auth.oauth.service import register_client

@pytest.mark.asyncio
async def test_auth(
    notification_service: NotificationService,
    user_service: UserService, 
):
    await clean_up(
        notification_service, user_service, 
        emails=[CONTACT_EMAIL]
    )
    await crud(user_service)
    await clean_up(
        notification_service, user_service, 
        emails=[CONTACT_EMAIL]
    )
    pass


async def clean_up(
    notification_service: NotificationService,
    user_service: UserService,
    **kwargs
):
    emails = kwargs.get("emails") or []
    user_ids = await user_service.find_ids(query={"email": {"$in": emails}})
    notification_ids = await notification_service.find_ids(query={"reference_id" : None})

    await user_service.delete_many(user_ids)
    await notification_service.delete_many(notification_ids)
    

async def crud(user_service: UserService):
    user_emails = [CONTACT_EMAIL]

    # bulk query
    users: List[UserList] = await user_service.find_many({
        "email": { "$in": user_emails}
    })
    assert {x.email for x in users} == set(user_emails)

    # user profile
    for x in users:
        user_info: dict = await user_service.find_info_and_files(x.id)
        assert user_info.get('avatar_src') is not None

    # user cache
    cache_users: List[UserList] = await user_service.cache_get_all()
    assert len(cache_users) == len(user_emails)
    assert {x.id for x in cache_users} == {x.id for x in users}

