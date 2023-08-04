import random
import string
import urllib
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from math import ceil, floor
from typing import Any, Iterable, List, Tuple, Union
from urllib.parse import urlparse

import numpy as np
from pydantic import BaseModel
import requests
from bson import ObjectId
from config.settings import DATE_STR_FORMAT
from dateutil.parser import parse
from fastapi import HTTPException

WEEK_IN_SECONDS = 60*60*24*7
MONTH_IN_SECONDS = 60*60*24*30
TIMEZONE_OFFSET = timedelta(hours=+7)
PRIMARY_TYPES = (bool, str, int, float, ObjectId)

def object_equal(a, b):
    """
    Compare two objects of type str, int, float, bool, ObjectId, dict or Iterable
    """
    if a == None:
        if (b != None): return False
    elif isinstance(a, PRIMARY_TYPES):
        if a != b: return False
    elif isinstance(a, dict):
        if len(a) != len(b): return False
        for f in a:
            if not object_equal(a[f], b[f]): return False
    elif isinstance(a, Iterable):
        if not array_equal(a, b): return False
    
    return True


def array_equal(a: Iterable, b: Iterable):
    """
    Compare two objects of type Iterable
    """
    if len(a) != len(b): return False
    for i in range(len(a)):
        if not object_equal(a[i], b[i]): return False
    return True


def get_changed_keys(a: Union[Iterable, dict], b: Union[Iterable, dict]):
    """
    Find the key with value changed when compare two objects of type dict
        - A_EXCESS : a - item = b
        - B_EXCESS : a + itme = b
    """
    keys = []
    if isinstance(a, dict) and isinstance(b, dict):
        for key in a:
            if isinstance(a[key], PRIMARY_TYPES): 
                if not a[key] == b[key]: keys.append(key)
            else: keys += [f"{key}.{x}" for x in get_changed_keys(a[key], b[key])]
        for key in b:
            if isinstance(b[key], PRIMARY_TYPES): 
                if not b[key] == a[key]: keys.append(key)
            else: keys += [f"{key}.{x}" for x in get_changed_keys(a[key], b[key])]
    elif isinstance(a, (list, tuple)) and isinstance(b,  (list, tuple)):
        for i in range(len(a)):
            if i < len(b): keys += get_changed_keys(a[i], b[i])
            else: keys.append('A_EXCESS')
        for i in range(len(b)):
            if i < len(a): keys += get_changed_keys(a[i], b[i])
            else: keys.append('B_EXCESS')
    return list(set(keys))

# urls
def url_encode(query: dict):
    single_query = {k: v for k,v in query.items() if not isinstance(v, list)}
    array_query = [f"{k}=" + f"&{k}=".join(v) for k, v in query.items() if isinstance(v, list)]
    encoded = urllib.parse.urlencode(single_query)
    if len(array_query) > 0: encoded += "&" + "&".join(array_query)
    return encoded


def check_site_exist(url):
    try:
        url_parts = urlparse(url)
        request = requests.head("://".join([url_parts.scheme, url_parts.netloc]))
        return request.status_code != HTTPStatus.NOT_FOUND
    except:
        return False

    
def split_data(data: List[Any], limit: int = 1000):
    n = ceil(len(data)/limit)
    indexes = (np.arange(n)*limit).tolist() + [len(data)]
    return [data[indexes[i]:indexes[i+1]] for i in range(n)]


def convert_key(key_map: dict, value: Any, key: str = None) -> dict:
    if key not in key_map and key is not None: return {key: value}
    if not isinstance(value, dict): 
        return {key_map[key]: value} if key is not None else {value: value}
    result = {}
    for k, v in value.items():
        result.update(convert_key(key_map, v, k))
    if key is None:
            return result
    return {key_map[key]: result}


def date_range(from_date, to_date) -> List[str]:
    date_range = []
    current_date = datetime.strptime(from_date, DATE_STR_FORMAT)
    while current_date <= datetime.strptime(to_date, DATE_STR_FORMAT):
        date_range.append(current_date.strftime(DATE_STR_FORMAT))
        current_date += timedelta(days=1)
    return date_range


def week_range(from_date, to_date) -> List[str]:
    dates = date_range(from_date, to_date)
    weeks = set()
    for x in dates:
        date = datetime.strptime(x, DATE_STR_FORMAT)
        weeks.add(f"{date.year}-w{date.isocalendar().week:02}")
    return sorted(list(weeks))
        

def parse_date(text: str):
    try:
        return datetime.strptime(text, DATE_STR_FORMAT).strftime(DATE_STR_FORMAT)
    except Exception:
        return None


def get_time(**kwargs):
    return datetime.utcnow().replace(tzinfo=timezone.utc) + timedelta(**kwargs)


def get_instance(py_class, data):
    if isinstance(data, BaseModel): data = data.dict()
    try: 
        return py_class(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_index(class_name, data, id):
    def processor() -> Tuple[int, class_name]:
        return next(((i, x) for i, x in enumerate(data) if x.id == id), (-1, None))
    if len(data) == 0: return lambda x = None : (-1, None)
    return processor


def get_random_string(length: int = 4):
    letters = string.ascii_uppercase
    return ''.join(random.choice(letters) for i in range(length))