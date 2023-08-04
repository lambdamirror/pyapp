import pathlib
from typing import Any, List

from _services.smtp.schema import *
from utils.logger import logger
from config.settings import *
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema
from jinja2 import Environment, FileSystemLoader, select_autoescape


conf = ConnectionConfig(
    MAIL_USERNAME=NOTIFICATION_EMAIL,
    MAIL_PASSWORD=NOTIFICATION_EMAIL_PASSWORD,
    MAIL_FROM=NOTIFICATION_EMAIL,
    MAIL_FROM_NAME=MAIL_FROM_NAME,
    MAIL_PORT=465,
    MAIL_SERVER=MAIL_SERVER,
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)


async def send_text(email_addresses: List[str], body) -> dict:
    message = MessageSchema(
        subject="Text Messages",
        # List of recipients, as many as you can pass
        recipients=email_addresses,
        body=body,
        subtype="plain"
    )

    fm = FastMail(conf)
    await fm.send_message(message)

    return {"message": "email has been sent"}


async def send_html(data: EmailSchema) -> dict:

    message = MessageSchema(
        subject=data.subject,
        # List of recipients, as many as you can pass
        recipients=data.recipients,
        cc=data.cc,
        body=data.body,
        subtype='html'
    )
    fm = FastMail(conf)
    await fm.send_message(message)

    return {"message": "email has been sent"}


async def send_template(template_name, data: EmailSchema, **kwargs) -> dict:
    logger.info(f"[SMTP] send_template <{template_name}> to:{data.recipients} cc:{data.cc}")
    try:
        env = Environment(
            loader=FileSystemLoader(searchpath=f"{pathlib.Path(__file__).parent.resolve()}/templates"),
            autoescape=select_autoescape(["html", "xml"])
        )
        template = env.get_template(f"{template_name}.html")

        return await send_html(data=EmailSchema(**{
            **data.dict(),
            "body": template.render(**kwargs),
        }))
    except Exception as e:
        return {'message': str(e)}



