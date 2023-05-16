from _documents.logs.service import logging_service
from _documents.notifications.service import notification_service


JOB_SCHEDULE = [
    {
        "func": logging_service.clean_up,
        "trigger": "cron",
        "day_of_week": "*",
        "hour": 0,
        "minute": 0,
        "second": 0,
        "args": [90]
    },
    {
        "func": notification_service.clean_up,
        "trigger": "cron",
        "day_of_week": "*",
        "hour": 0,
        "minute": 0,
        "second": 0,
        "args": [90]
    }
]