import json
from datetime import timedelta

import dateutil.parser as date_parser
import pytest
from utils.logger import logger
from config.settings import *
from fastapi import HTTPException
from config.conftest import handle_assert_error


@pytest.mark.asyncio
async def test_webhook_service():
    try:
        webhook()
    except Exception as e:
        if isinstance(e, HTTPException): logger.error(e.detail)
        if isinstance(e, AssertionError): handle_assert_error()


def webhook():
    data = {
    }
