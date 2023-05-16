from motor.motor_asyncio import AsyncIOMotorClient
from config.settings import *
from _documents.users.schema import Role

class MongoDbClient():
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(MongoDbClient, cls).__new__(cls)
        return cls.instance
    
    def __init__(self):
        self.conn = AsyncIOMotorClient(MONGODB_CONN_STR)
        self.users = self.conn[USERS_DB_NAME]
        self.accounts = self.conn[ACCOUNTS_DB_NAME]
        self.settings = self.conn[SETTINGS_DB_NAME]

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
        if name in Role.list():
            return self.users[name]
        if name in ['reset-token', 'notification']:
            return self.accounts[name]
        
        return None
    

