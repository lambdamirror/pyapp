import urllib
import os

# Environment Variables
API_ENV=os.environ.get("API_ENV")

API_URL=os.environ.get("API_URL")

FRONT_END_URL=os.environ.get("FRONT_END_URL")

REDIS_URL=os.environ.get("REDIS_URL")

MONGODB_CONN_STR=os.environ.get("MONGODB_CONN_STR")

PAYPAL_CLIENT_ID=os.environ.get("PAYPAL_CLIENT_ID")

PAYPAL_SECRET=os.environ.get("PAYPAL_SECRET")

GMAIL_PUBSUB_ACTIVE=True if os.environ.get("GMAIL_PUBSUB_STATUS") == "active" else False

DBA_EMAIL=os.environ.get("DBA_EMAIL")

CONTACT_EMAIL=os.environ.get("CONTACT_EMAIL")

NOTIFICATION_EMAIL=os.environ.get("NOTIFICATION_EMAIL")
NOTIFICATION_EMAIL_PASSWORD=os.environ.get("NOTIFICATION_EMAIL_PASSWORD")
MAIL_FROM_NAME=os.environ.get("MAIL_FROM_NAME")
MAIL_SERVER=os.environ.get("MAIL_SERVER")

DO_SPACES_KEY=os.environ.get("DO_SPACES_KEY")
DO_SPACES_SECRET=os.environ.get("DO_SPACES_SECRET")

CORS_ORIGINS=os.environ.get("CORS_ORIGINS") if os.environ.get("CORS_ORIGINS") is not None else ""

# App Variables
API_SECRET_KEY="api_secret"

AUTH_SECRET_KEY="auth_secret"

API_ALGORITHM='HS256'

API_ACCESS_TOKEN_EXPIRE_MINUTES=10080

HOST="0.0.0.0"

PORT=8000

DEBUG_MODE=API_ENV in ['dev']

MAX_QUERY_LENGTH=10000

MAX_FETCH_LIMIT = 200

DATE_STR_FORMAT='%Y-%m-%d'

FULL_DATE_STR_FORMAT = "%b %d, %Y %H:%M:%S"

S3_REGION=[{ 'id': 'nyc3', 'value': 'USA'}, { 'id': 'sgp1', 'value': 'Singapore'}]



