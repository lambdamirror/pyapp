
import json
from urllib.parse import parse_qs, urlparse

from authlib.integrations.starlette_client import OAuth, OAuthError
from bson import ObjectId
from fastapi import APIRouter, BackgroundTasks, Request
from starlette.config import Config

from _services.smtp.schema import EmailSchema
from _services.smtp.service import send_template
from _documents.users.schema import Role, User, UserList
from _documents.users.service import user_service
from auth.jwt import CREDENTIALS_EXCEPTION, create_token
from auth.oauth.service import verify_token
from config.settings import *
from _services.mongo.service import MongoDbClient

from _services.redis.service import RedisClient


# OAuth configs
GOOGLE_CLIENT_ID = "943025872266-s9m6u4t85rq3c0cg61ioth4ftoqfb32q.apps.googleusercontent.com" or None
GOOGLE_CLIENT_SECRET = "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" or None
if GOOGLE_CLIENT_ID is None or GOOGLE_CLIENT_SECRET is None:
    raise BaseException('Missing env variables')

# Set up OAuth
config_data = {'GOOGLE_CLIENT_ID': GOOGLE_CLIENT_ID,
               'GOOGLE_CLIENT_SECRET': GOOGLE_CLIENT_SECRET}
starlette_config = Config(environ=config_data)
oauth = OAuth(starlette_config)
oauth.register(
    name='google',
    # client_id=GOOGLE_CLIENT_ID,
    # client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
)
# Frontend URL:
REDIRECT_URL = f'{API_URL}/auth/google/redirect'


async def create_new_user(background_tasks: BackgroundTasks, 
                          email: str, name: str = None, client_id = None):
    roles = [Role.USER.value]
    user_data =  User(
        email=email, name=name, 
        client_id=client_id, roles=roles,
        status='ACTIVE'
    )
    insert_result = await MongoDbClient().get_docs('user').insert_one(user_data.dict())
    new_user = await user_service.find({"_id": insert_result.inserted_id})

    await user_service.cache_update(new_user)
    return new_user


async def authorize_redirect(request: Request, client_id: str):
    google = oauth.create_client('google')
    redirect = await google.authorize_redirect(request, REDIRECT_URL)
    # cache mapping client_id to google_state
    location = dict(redirect.headers).get("location")
    query = parse_qs(urlparse(location).query)
    await RedisClient().set_cache(client_id, f"_state_google_{query['state'][0]}")
    return redirect


async def auth(request: Request, background_tasks: BackgroundTasks):
    client_id = None
    for key in request.session:
        if (client_id := await RedisClient().get_cache(key)) is not None:
            await RedisClient().delete_cache(key)
            break
    try:
        google = oauth.create_client('google')
        token = await google.authorize_access_token(request)
    except OAuthError as e:
        # clear sessions
        for key in list(request.session.keys()):
            request.session.pop(key, None)
        raise CREDENTIALS_EXCEPTION

    user_data: dict = token.get("userinfo")
    authorized_user = await user_service.find({
        'email': user_data['email']
    })
    if authorized_user is None:
        authorized_user = await create_new_user(background_tasks,
                                                user_data['email'], user_data.get('name'), client_id)
        background_tasks.add_task(send_template,
            "welcome", 
            EmailSchema(**{
                "subject": f"Welcome to PhtCreative Studio",
                "recipients": [authorized_user.email],
                "cc": [],
            }),
            **{
                "first_name": authorized_user.name or authorized_user.email,
                "url": FRONT_END_URL
            }
        )
    elif authorized_user.status == 'PENDING':
        user_doc = await user_service.db_client().find_one({ 'email': user_data['email'] })
        await verify_token(user_doc['verify_token'], background_tasks)
        authorized_user = await user_service.find({ 'email': user_data['email'] })
    
    background_tasks.add_task(user_service.push_login_info, request, authorized_user)
    return {'result': True, 'access_token': create_token(authorized_user)}
