import json
from datetime import datetime
from io import BytesIO
from typing import List

from fastapi import HTTPException

from _services.s3._shared.base import S3BaseClient
from _services.s3._shared.schema import (FILE_TYPES, MasterNode,
                                         ObjectMetaData, S3BaseConfig)
from config.settings import *
from utils.logger import logger


class S3ClientManager():

        def __init__(self, clients: List[S3BaseClient] = []):
            self.clients = clients
        
        @staticmethod
        def define_path(path: str = ""):
            paths = path.split('/')
            if len(paths) == 0 or '' in paths[:-1]: return None, None
            return paths[0], '/'.join(paths[1:])


        def add_client(self, client: S3BaseClient):
            self.clients.append(client)


        def get_client(self, region: str = "sgp1", provider: str = "do"):
            return next((
                x for x in self.clients if x.config.provider == provider and x.config.region_name == region
            ), None)


s3_manager = S3ClientManager()
## add DO s3 clients
for region_name in ["sgp1", "nyc3"]:
    s3_manager.add_client(S3BaseClient(
        config=S3BaseConfig(**{
            "provider": "do",
            "region_name": region_name,
            "endpoint_url": f"https://{region_name}.digitaloceanspaces.com",
            "aws_access_key_id": DO_SPACES_KEY,
            "aws_secret_access_key": DO_SPACES_SECRET
        })
    ))