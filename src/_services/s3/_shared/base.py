import json
import os
import pathlib
import zipfile
from io import BytesIO

import boto3
import pandas as pd
from botocore.exceptions import ClientError
from fastapi import HTTPException
from PIL import Image

from config.settings import *
from utils.helper import WEEK_IN_SECONDS, split_data
from utils.logger import logger

from .schema import *


class S3BaseClient():

    def __init__(self, config: S3BaseConfig) -> None:
        self.config = config
        self.client = boto3.client('s3',
           **{k: v for k, v in config.dict().items() if v is not None and k not in ['provider']}
        )
     
        self.bucket = f"{config.provider}{'-' + config.region_name if config.region_name is not None else 'global'}{f'-{API_ENV}'}"
        self.expiration = WEEK_IN_SECONDS


    @staticmethod
    def __get_safe_ext(ext: str):
        ext = ext.upper()
        if ext in ['JPG', 'JPEG']:
            return 'JPEG' 
        elif ext in ['PNG']:
            return 'PNG' 
        else:
            raise Exception('Extension is invalid') 


    def get_presigned_url(self, key):
        """
        Return presigned url to download and view
        """
        if key[-1] == '/': return None
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return self.client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket,
                        'Key': key},
                ExpiresIn=self.expiration
            )
        except Exception as err:
            return None


    def get_presigned_post(self, key, fields=None):
        """
        Return presigned post url
        """
        return self.client.generate_presigned_post(
            self.bucket,
            key + "${filename}" if key[-1] == '/' else key,
            Fields=fields,
            Conditions=[["starts-with", "$key", key]] if key[-1] == '/' else [],
            ExpiresIn=self.expiration
        )
    
    
    def put_object(self, key: str, data = None):
        try:
            if data is not  None:
                self.client.put_object(Body=data, Bucket=self.bucket, Key=key)
            else:
                self.client.put_object(Bucket=self.bucket, Key=key)
            return self.get_presigned_url(key)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


    def upload_object(self, data, key: str):
        self.client.upload_fileobj(data, Bucket=self.bucket, Key=key)
        return self.get_presigned_url(key)


    def delete_objects(self, paths: List[str] = []):
        """Delete objects"""
        data = []
        not_found = []
        for x in paths:
            _, object_list = self.list_objects(x, directory=(x[-1]=='/'))
            if len(object_list) == 0:
                not_found.append(x)
                continue
            if x[-1] == '/':
                data += [{'Key': xx['Key']} for xx in object_list]
            else:
                data.append({'Key': f"{x.strip('/')}"})
        if len(not_found):
            raise HTTPException(status_code=400, detail=f"Path {', '.join(not_found)} not found.")
        data_splited = split_data(data, 1000)
        deleted_keys = []
        for objects in data_splited:
            objects_to_delete = [{'Key': o['Key']} for o in objects]
            r = self.client.delete_objects(Bucket=self.bucket, Delete={'Objects': objects_to_delete})
            if r.get('Deleted') is not None: deleted_keys += [x['Key'] for x in r.get('Deleted')]
        return {
            'deleted_keys': list(dict.fromkeys(deleted_keys))
        }


    def create_directory(self, key: str = ""):
        if isinstance(key, str) and len(key) > 0:
            key = key.strip('/') + '/'
            self.put_object(key)
            return self.get_presigned_post(key)


    def list_objects(self, path: str = None, directory = True):
        """
        Return metadata of objects
        """
        prefix = ""
        if path is not None: prefix += path.strip('/') + ('/' if directory else '')
        marker = None
        objects  = []
        while True:
            if marker is not None:
                r = self.client.list_objects(Bucket=self.bucket, Prefix=prefix, Marker=marker)
            else:
                r = self.client.list_objects(Bucket=self.bucket, Prefix=prefix)
            if r.get('Contents') is not None: 
                if not directory:
                    objects += [x for x in r.get('Contents') if x['Key'][-1] != '/']
                else:
                    objects += r.get('Contents')
            if not r.get('IsTruncated'): break
            marker = r.get('NextMarker')
        return prefix, objects
  

    def get_post_data(self, paths: List[str], directory = True, fields=None):
        """
        Return a presigned URL S3 POST request to upload files
        Handle missing objects for parent folders
        """
        if len(paths) == 0:
            raise HTTPException(status_code=400, detail=f'Valid path not found.')
        results = []
        object_put = []
        for path in paths:
            # Generate a presigned S3 POST URL
            prefix = ""
            if path is not None: prefix += f"{path.strip('/')}"

            try:
                results.append({
                    **self.get_presigned_post(
                        prefix + '/' if directory else prefix,
                        fields=fields
                    ),
                    **{'path': path}
                })
                # put objects for parent folders
                parents = path.strip('/').split('/')[:-1]
                if directory: parents = path.strip('/').split('/')
                for i in range(len(parents)+1): 
                    new_key = '/'.join(parents[:i]) + '/'
                    if new_key in object_put: continue
                    object_put.append(new_key)
                    self.put_object(new_key)
            except ClientError as e:
                raise HTTPException(status_code=400, detail=str(e))

        # The response contains the presigned URL and required fields
        return results


    def get_display_data(self, path: str = None, allow_upload: bool = True):
        """
        Return displaying data when select a folder 
        """
        prefix, object_list = self.list_objects(path)
        if len(object_list) == 0:
            # raise HTTPException(status_code=400, detail=f"Path {path} not found.")
            return None
        try:
            objects: List[ObjectMetaData] = []
            for x in object_list:  
                full_obj_path = x['Key'].strip('/').split('/')
                rel_obj_path = [prefix[:-1], *x['Key'].split(prefix)[-1].split('/')]
                if x['Key'][-1]=='/':
                    depth = len(rel_obj_path) - 2
                    title = full_obj_path[-1]
                    object_type = 'folder'
                    extension = None
                else:
                    depth = len(rel_obj_path) - 1
                    title = rel_obj_path[-1]
                    object_type = 'file'
                    extension = x['Key'].split('.')[-1].lower()
                    for k, v in FILE_TYPES.items():
                        if extension in v: object_type = k; break

                if depth < 2:
                    objects.append(ObjectMetaData(**{
                        'key': x['Key'],
                        'path': '/'.join(x['Key'].split('/')[2:]).strip('/'),
                        'title': title,
                        'depth': depth,
                        'object_type': object_type,
                        'extension': extension,
                        'size': x['Size'],
                        'modified_at': x['LastModified'].timestamp(),
                        'url': self.get_presigned_url(x['Key']) , 
                        'presigned_post': self.get_presigned_post(x['Key']) if allow_upload else None,
                    }))

            if (master_node := next((x for x in objects if x.depth == 0), None)) is None:
                # raise HTTPException(status_code=400, detail=str(f'Path {path} not found'))
                return None

            return json.loads(MasterNode(
                **master_node.dict(),
                children=[x for x in objects if x.depth == 1]
            ).json())

        except ClientError as e:
            raise HTTPException(status_code=400, detail=str(e))


    def copy_object():
        """
        Require source: str, destination: str, directory: boolean. Only allows in Output
        """
        pass


    def rename_object(self, source: str, name: str):
        """
        Rename a file or directory
        """
        if source == '' or name == '': 
            raise HTTPException(status_code=400, detail=f"Empty source or name are not allowed.")
        data = []
        _, object_list = self.list_objects(source, directory=(source[-1]=='/'))
        if len(object_list) == 0:
            raise HTTPException(status_code=404, detail=f"Object path {source} not found")

        parent_path = '/'.join(source.strip('/').split('/')[:-1])
        if source[-1] == '/':
            for obj in object_list:
                relative_path = obj['Key'].split(source.strip('/') + '/')[-1]
                new_key = f"{parent_path}/{name}/{relative_path}"
                data.append({
                    'source': obj['Key'], 
                    'destination': new_key
                })
        else:
            data.append({'source': source, 'destination': f"{parent_path}/{name}"})

        rename_data = []
        for x in data:
            r = self.client.copy_object(
                Bucket=self.bucket, 
                CopySource={'Bucket': self.bucket, 'Key': x['source']}, Key=x['destination']
            )
            if r.get('CopyObjectResult') is not None:
                rename_data.append({'key': x['source'], 'new_key': x['destination']})

        data_splited = split_data(rename_data, 1000)
        for objects in data_splited:
            objects_to_delete = [{'Key': o['key']} for o in objects]
            r = self.client.delete_objects(Bucket=self.bucket, Delete={'Objects': objects_to_delete})

        return {
            'renamed': [{
                'source': x['key'],
                'data': {
                    'key': x['new_key'],
                    'path': '/'.join(x['new_key'].split('/')[2:]).strip('/'),
                    'title': name,
                    'extension': x['new_key'].split('.')[-1].lower() if '.' in x['new_key'] else None,
                    'modified_at': datetime.utcnow().timestamp(),
                    'url': self.get_presigned_url(x['new_key']) , 
                    'presigned_post':  self.get_presigned_post(x['new_key']),
                }
            } for x in rename_data]
        }


    def objects_to_zip(self, keys: List[str], path: str = None):
        if path is not None: path = path.strip('/') + '/'
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_DEFLATED) as zip_file:
            for key in keys:
                if path is not None: fileName = key.split(path)[-1]
                else: fileName = os.path.basename(key)
                if fileName == '': continue
                try:
                    response = self.client.get_object(Bucket=self.bucket, Key=key)
                    zip_file.writestr(fileName, response['Body'].read())
                except Exception as e:
                    logger.error(f"{key} : {e}")
        buffer.seek(0)
        return buffer


    def resize_image_object(self, key: str, size: tuple = (1500, 1000)):
        extension = key.split('.')[-1].lower()
        if extension not in FILE_TYPES['image-preview']:
            return None
        _, objects = self.list_objects(key, directory=False)
        if len(objects) == 0: return None
        file_byte_string = self.client.get_object(Bucket=self.bucket, Key=key)['Body'].read()
        image = Image.open(BytesIO(file_byte_string))
        image.thumbnail(size)

        # Build web version
        display = BytesIO()
        image.copy().save(display, self.__get_safe_ext(extension))
        display.seek(0)

        preview = BytesIO()
        image.save(preview, self.__get_safe_ext(extension))
        preview.seek(0)

        return {
            'display': display,
            'preview': preview
        }


    def read_object(self, key: str):
        extension = key.split('.')[-1].lower()
        _, objects = self.list_objects(key, directory=False)
        if len(objects) == 0: return None
        file_byte_string = self.client.get_object(Bucket=self.bucket, Key=key)['Body'].read()
        if extension in ["xls", "xlsx"]:
            # excel_object = pd.ExcelFile(BytesIO(file_byte_string), engine='xlrd')
            # dt_1 = excel_object.parse(sheet_name = 'Sheet1', index_col = 0)
            # return dt_1
            return pd.read_excel(BytesIO(file_byte_string))
            
        return None
        

