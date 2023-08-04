
import pathlib
from typing import List

from _services.gmail._base.schema import GmailBaseConfig
from _services.gmail._base.service import GmailBaseClient
from utils.logger import logger

class GmailSalesClient(GmailBaseClient):


    def __init__(self, *args, **kwargs):
        super(GmailSalesClient, self).__init__(*args, **kwargs)


    def add_message(self, message_id: str):    
        self.messages_queue.put(message_id)


    async def handle_messages(self):
        """
        Cron job
        """
        queue_size = self.messages_queue.qsize()
        if queue_size == 0: return
        for i in range(queue_size):
            message_id = self.messages_queue.get(timeout=2)
            payload = self.get_message(message_id)
            if payload.get('headers') is None or payload.get('body') is None: return
            sender = self.get_header(payload, "From").split(' ')[-1].strip('<>')
            try:
                # handle email messages here
                pass
            except Exception as e:
                logger.error(e)

gmail_sample_client = GmailSalesClient(config=GmailBaseConfig(**{
    'user_id': 'email@sample.com',
    'service_account_file': f'{pathlib.Path(__file__).parent.resolve()}/gmail-api-secret-key.json',
    'project_id': 'project_id',
    'topic_id': "topic_id",
    'subscription_id': "subscription_id"
}))



