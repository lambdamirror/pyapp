from datetime import datetime
from typing import Any, List

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
    region_name: str | None
    endpoint_url: str
    aws_access_key_id: str
    aws_secret_access_key: str
    config: Any | None

    class Config(BaseConfig):
        pass


class ObjectMetaData(BaseModel):
    key: str | None
    path: str | None
    title: str | None
    depth: int | None
    object_type: str = Field("folder")
    folder_type: str | None
    extension: str | None
    size: float | None
    modified_at: datetime | None
    url: str | None
    presigned_post: Any
     
    class Config(BaseConfig):
        pass

class MasterNode(ObjectMetaData):
    children: List[ObjectMetaData]

class OrderFolders(BaseModel):
    input: MasterNode | None
    output: MasterNode | None
    preview: MasterNode | None