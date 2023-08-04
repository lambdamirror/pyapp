import asyncio
import sys
import traceback

from pytest_asyncio import fixture

from _documents._base.schema import ServiceBaseConfig
from _documents.notifications.schema import *
from _documents.notifications.service import NotificationService
from _documents.users.schema import *
from _documents.users.service import UserService
from _services.mongo.service import MongoDbClient
from utils.logger import logger

# import pytest

class RequestClone(BaseModel):
    query_params: dict


def handle_assert_error():
    _, _, tb = sys.exc_info()
    traceback.print_tb(tb) # Fixed format
    tb_info = traceback.extract_tb(tb)
    filename, line, func, text = tb_info[-1]

    print('An error occurred on line {} in statement {}'.format(line, text))
    exit(1)

SCOPE = "session"


@fixture(scope="session")
def event_loop():
    return asyncio.get_event_loop()


# Services
@fixture(scope=SCOPE)
async def notification_service() -> NotificationService:
    service = NotificationService(ServiceBaseConfig(**{
        "document": "notification",
        "py_create_class": NotificationCreate,
        "py_update_class": None,
        "py_list_class": NotificationList,
        "py_master_class": Notification,
        "mongodb_client": MongoDbClient(),
    }))
    await service.cache_clear()
    return service


@fixture(scope=SCOPE)
async def user_service() -> UserService:
    service = UserService(ServiceBaseConfig(**{
        "document": "user",
        "py_list_class": UserList,
        "mongodb_client": MongoDbClient()
    }))
    await service.cache_clear()
    return service

