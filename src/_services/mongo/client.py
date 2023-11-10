from motor.motor_asyncio import AsyncIOMotorClient
from config.settings import *
from utils.logger import logger


class MongoDbClient():
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(MongoDbClient, cls).__new__(cls)
        return cls.instance
    
    def __init__(self):
        self.conn = AsyncIOMotorClient(MONGODB_CONN_STR)
        self.accounts = self.conn['Accounts']
        self.settings = self.conn['Settings']

    def disconnect(self):
        self.conn.close()

    async def get_server_info(self, db: str):
        '''
        Get Database server info
        '''
        try:
            return await getattr(self, db).server_info()
        except Exception:
            raise Exception("Unable to connect to the server.")
    
    def get_docs(self, name: str):
        if name in ['users', 'reset-token', 'notification', 'logs']:
            return self.accounts[name]
        if name in ['settings']:
            return self.settings[name]
        return None
    
