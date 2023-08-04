

import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import json
from threading import Thread
from typing import Any, List

from utils.logger import logger
from utils.schema import OrderedSetQueue
from config.settings import *
from google.cloud import pubsub_v1
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .schema import GmailBaseConfig, MessageStatus


class GmailBaseClient():

    def __init__(self, config: GmailBaseConfig) -> None:
        self.config = config
        self.credentials = service_account.Credentials.from_service_account_file(
            config.service_account_file, 
            scopes=config.scopes,
            subject=config.user_id
        )
        self.watch()
        self.messages_queue = OrderedSetQueue(maxsize=0)
        self.message_count = 0
        self.thread = Thread(target=self.subscribe)
        self.subscriber = pubsub_v1.SubscriberClient(
            credentials=service_account.Credentials.from_service_account_file(config.service_account_file)
        )
        self.subscription_path = self.subscriber.subscription_path(config.project_id, config.subscription_id)
        if GMAIL_PUBSUB_ACTIVE: 
            self.thread.start()
            logger.info(f"{self.__class__.__name__} is running.")


    @staticmethod
    def get_header(payload, name: str):
        return next((x for x in payload['headers'] if x['name'] == name), {}).get('value')


    def unsubscribe(self):
        if not GMAIL_PUBSUB_ACTIVE: return
        logger.info(f"Close {self.__class__.__name__} subscription.")
        self.streaming_pull_future.cancel()
        self.streaming_pull_future.result()
        self.thread.join()


    def subscribe(self):
        # Wrap subscriber in a 'with' block to automatically call close() when done.
        self.streaming_pull_future = self.subscriber.subscribe(self.subscription_path, callback=self.callback)
        with self.subscriber:
            try:
                # When `timeout` is not set, result() will block indefinitely,
                # unless an exception is encountered first.
                self.streaming_pull_future.result()
            except TimeoutError:
                self.streaming_pull_future.cancel()  # Trigger the shutdown.
                self.streaming_pull_future.result()  # Block until the shutdown is complete.

    
    def watch(self):
        service = build('gmail', 'v1', credentials=self.credentials)
        result = service.users().watch(userId=self.config.user_id, body={
            "labelFilterAction": "include",
            "labelIds": ["INBOX"],
            "topicName": self.config.topic_id
        }).execute()
        if (history_id := result.get("historyId")) is not None:
            self.config.history_id = history_id
        else:
            logger.warn(f"{self.__class__.__name__}.watch() failed: {result}")


    def list_history(self, start_id: str, max_results: int = 500):
        service = build('gmail', 'v1', credentials=self.credentials)
        history_list = []
        while len(history_list) < max_results:
            results = None
            try:
                results = service.users().history().list(
                    userId=self.config.user_id, maxResults=max_results,
                    startHistoryId=start_id, historyTypes=["messageAdded"]
                ).execute()
                if results.get('history') is None: break
                history_list += results.get('history')
                start_id = history_list[-1].get('id')
                if len(results.get('history')) < max_results: break
            except (HttpError, OSError) as e:
                logger.warn(f"{self.__class__.__name__}.list_history() failed start_id={start_id}: {results if results is not None else e}")
                break

        return history_list


    def list_messages(self, query: str, max_results: int = 500):
        service = build('gmail', 'v1', credentials=self.credentials)
        results = None
        try:
            results = service.users().messages().list(
                userId=self.config.user_id, maxResults=max_results,
                q=query
            ).execute()
            return results.get('messages')
        except (HttpError, OSError) as e:
            logger.warn(f"{self.__class__.__name__}.list_messages() failed: {results if results is not None else e}")
            return []


    def get_message(self, id: str):
        service = build('gmail', 'v1', credentials=self.credentials)
        result = None
        try:
            result = service.users().messages().get(
                userId=self.config.user_id, id=id
            ).execute()
            return result.get('payload')

        except (HttpError, OSError) as e:
            logger.warn(f"GmailClient.get_message() failed: {result if result is not None else e}")
            return None


    def get_message_content(self, id: str):
        body_data = None
        payload = self.get_message(id)
        if payload is None: return { 'headers': [], 'body': None}

        mime_type = payload.get('mimeType')
        if mime_type == 'text/html':
            body_data = payload.get('body').get('data') if payload.get('body') is not None else None
        elif mime_type in ['multipart/mixed', 'multipart/alternative']:
            text_part = next((x for x in payload.get('parts') if x.get('mimeType') == 'text/html'), {})
            body_data = text_part.get('body').get('data') if text_part.get('body') is not None else None

        return {
            'headers': payload.get('headers') if 'headers' in payload else [],
            'body': base64.urlsafe_b64decode(
                body_data + '=' * (4 - len(body_data) % 4)
            ).decode('utf-8') if body_data is not None else None
        }   


    def send_message(self, to_email: str, payload: Any):
        service = build('gmail', 'v1', credentials=self.credentials)
        mime_type = payload.get('mimeType')

        # build MIME object
        msg = MIMEMultipart('alternative')
        msg['To'] = to_email
        for x in payload.get('headers'):
            if x['name'] == 'Subject': msg['Subject'] = x['value']
            if x['name'] == 'From': 
                msg['From'] = x['value']

        if mime_type == 'text/html':
            msg.attach(MIMEText(payload.get('body').get('data'), 'html'))
        elif mime_type in ['multipart/mixed', 'multipart/alternative']:
            for x in payload.get('parts'):
                if x.get('mimeType') == 'text/html':
                    body_data = x.get('body').get('data')
                    data = base64.urlsafe_b64decode(
                        x.get('body').get('data') + '=' * (4 - len(body_data) % 4)
                    ).decode('utf-8')
                    msg.attach(MIMEText(data, 'html'))
        
        # forward the message
        results = None
        try:
            results = service.users().messages().send(
                userId=self.config.user_id, body={
                  'raw': base64.urlsafe_b64encode(msg.as_string().encode()).decode()
                }
            ).execute()
            return 
           
        except (HttpError, OSError, Exception) as e:
            logger.warn(f"{self.__class__.__name__}.forward_message() failed: {results if results is not None else e}")


    def list_filter(self):
        service = build('gmail', 'v1', credentials=self.credentials)
        results = None
        try:
            results = service.users().settings().filters().list(
                userId=self.config.user_id
            ).execute()
            
            return results.get('filter') if results.get('filter') is not None else []
           
        except (HttpError, OSError) as e:
            logger.warn(f"{self.__class__.__name__}.list_filter() failed: {results if results is not None else e}")
            return []


    def create_filter(self, criteria_from: List[str], forward_to: str):
        service = build('gmail', 'v1', credentials=self.credentials)
        results = None
        try:
            if len(criteria_from) > 500: 
                raise Exception(f"Too many emails ({len(criteria_from)}). Max = 500.")

            results = service.users().settings().filters().create(
                userId=self.config.user_id, body={
                    'criteria': {
                        'from': ' OR '.join(criteria_from)
                    },
                    'action': {
                        'forward': forward_to,
                    }
                }
            ).execute()
            return 
           
        except (HttpError, OSError, Exception) as e:
            logger.warn(f"{self.__class__.__name__}.create_filter() failed: {results if results is not None else e}")


    def delete_filter(self, filter_id: str):
        service = build('gmail', 'v1', credentials=self.credentials)
        results = None
        try:
            results = service.users().settings().filters().delete(
                userId=self.config.user_id, id=filter_id
            ).execute()
            return 
           
        except (HttpError, OSError) as e:
            logger.warn(f"{self.__class__.__name__}.delete_filter() failed: {results if results is not None else e}")


    def handle_message(self, message_id: str):
        pass


    def callback(self, message: pubsub_v1.subscriber.message.Message):
        message_data = json.loads(message.data.decode('utf-8'))
        self.message_count += 1
        logger.info(f"[{self.__class__.__name__} #{self.message_count}] Received history_id : {self.config.history_id} -> {message_data.get('historyId')}")
        message.ack()

        history_list = []
        if self.config.history_id != '':
            history_list = self.list_history(self.config.history_id)
            self.config.history_id = message_data.get('historyId')

        if len(history_list) == 0: return
        messages = []
        for x in history_list:
            messages += x.get('messagesAdded') if x.get('messagesAdded') is not None else []

        for x in set([xx.get('message').get('id') for xx in messages]): 
            self.handle_message(x)


    def get_process_status(self):
        return {
            'message_count': self.message_count,
            'messages_queue': list(self.messages_queue.queue),
            'qsize': self.messages_queue.qsize(),
            'config': json.loads(self.config.json()),
        }





