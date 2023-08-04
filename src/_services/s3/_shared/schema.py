from datetime import datetime
from typing import Any, List, Union

from utils.schema import BaseConfig, PyObjectId
from pydantic import BaseModel, Field

FILE_TYPES = {
    'image-preview': ['jpg', 'png'],
    'image': ['nef', 'cr2', 'cr3'],
    'text': ['txt'],
    'zip': ['zip', 'rar', 'iso'],
    'video-preview': ['mp4', 'mov', 'mp3', 'm4a','wav'],
}


class S3BaseConfig(BaseModel):
    provider: str
    region_name: Union[None, str]
    endpoint_url: str
    aws_access_key_id: str
    aws_secret_access_key: str
    config: Union[None, Any]

    class Config(BaseConfig):
        pass


class ObjectMetaData(BaseModel):
    key: Union[None, str]
    path: Union[None, str]
    title: Union[None, str]
    depth: Union[None, int]
    object_type: str = Field("folder")
    folder_type: Union[None, str]
    extension: Union[None, str]
    size: Union[None, float]
    modified_at: Union[None, datetime]
    url: Union[None, str]
    presigned_post: Any
     
    class Config(BaseConfig):
        pass

class MasterNode(ObjectMetaData):
    children: List[ObjectMetaData]

class OrderFolders(BaseModel):
    input: Union[None, MasterNode]
    output: Union[None, MasterNode]
    preview: Union[None, MasterNode]