from typing import List

from _documents.notifications.service import notification_service

from _documents.users.schema import *
from _documents.users.service import user_service
from config.settings import DATE_STR_FORMAT, S3_REGION
from utils.helper import get_instance, parse_date


# API
async def get_profile_info(user: UserList):
    user_info = await user_service.find_info_and_files(user.id)
    amounts = 0
    estimated = 0
    noti_results: dict = await notification_service.find_by_user(user)
    notifications = noti_results.get('items') 
    
    return {
        'user': user_info,
        'balance': {'amounts': amounts, 'estimated': estimated, 'base_currency': 'USD'},
        'notifications': notifications,
        'options': {
            'gender': USER_GENDER,
            'email_topic': EMAIL_TOPICS,
            'storage_region': [x['id'] for x in S3_REGION],
            'total_notifications': noti_results.get('total_count'),
            'hidden_unread_notifications': noti_results.get('unread_count') - len([x for x in notifications if x['status'] == 'UNREAD'])
        },
    }


async def update_profile(user: UserList, data: UserUpdate):
    return { 'data': await user_service.update(data) }


async def get_billing_data(user: UserList, skip: int = 0):
    pending_bills = []
    payment_history = []
    return {
        'pending_bills': pending_bills,
        'payment_history': payment_history
    }


async def get_notifications(user: UserList, skip: int = 0, limit: int = 10):
    results: dict = await notification_service.find_by_user(user, skip=skip, limit=limit)
    return {
        'data': results.get('items'),
        'options': {
            'total_notifications': results.get('total_count'),
            'hidden_unread_notifications': results.get('unread_count') - len([x for x in results.get('items') if x['status'] == 'UNREAD'])
        }
    }


async def mark_read_notifications(user: UserList, mode, notification_ids: List[str]):
    results = await notification_service.mark_as_read(user, mode, notification_ids)
    return {
        'data': results.get('items'),
        'options': {
            'hidden_unread_notifications': results.get('unread_count') - len([x for x in results.get('items') if x['status'] == 'UNREAD']) 
        }
    }



