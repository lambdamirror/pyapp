
import uuid
from time import sleep

import pytest
from schema import *
from service import *

from _services.smtp.service import send_template
from config.conftest import *

random_id = uuid.uuid4().hex[-5:]

render_args = {
    "registration": {
        "subject": f"Verify your email",
        "url": "https://example.com",
        "first_name": "First Name",
    },
    "welcome": {
        "subject": f"Welcome to PyApp [{uuid.uuid4().hex[-5:]}]",
        "url": "https://example.com",
        "first_name": "First Name",
    },
    "login": {
        "subject": f"Successful sign-in from new device [{uuid.uuid4().hex[-5:]}]",
        "email": CONTACT_EMAIL,
        "timestamp": "2023-01-03 04:03:59 GMT",
        "ip_address": "14.231.164.219",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36",
        "password_reset_url": "https://example.com"
    },
    "dba_initialization": {
        "subject": f"You are the first Database Admin at PyApp [{uuid.uuid4().hex[-5:]}]",
        "email": CONTACT_EMAIL,
        "username": CONTACT_EMAIL,
        "password": uuid.uuid4().hex,
        "contact_email": CONTACT_EMAIL,
    },
    "reset_email": {
        "subject": f"Email verification for your account [{uuid.uuid4().hex[-5:]}]",
        "first_name": "First Name",
        "email": CONTACT_EMAIL,
        "url": "https://example.com",
        "password_reset_url": "https://example.com",
    },
    "reset_password": {
        "subject": f"Password changed for your account [{uuid.uuid4().hex[-5:]}]",
        "first_name": "First Name",
        "email": "mail@example.com",
        "url": "https://example.com",
        "contact_email": CONTACT_EMAIL,
    },
}

@pytest.mark.asyncio
async def test_smpt_service():
    # await send_template
    assert True
    

async def template():
    for k, v in list(render_args.items())[-1:]:
        result: dict = await send_template(
            k,
            EmailSchema(**{
                **v,
                "recipients": [CONTACT_EMAIL],
            }),
            **v
        )
        assert result is not None
        sleep(5)