from typing import List

import pytest
from bson import ObjectId

from _services.s3.manager import s3_manager
from config.conftest import *
from utils.logger import logger
from config.settings import API_ENV, MONGODB_CONN_STR

@pytest.mark.asyncio
async def test_s3_manager():
    pass
