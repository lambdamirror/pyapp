import json
from pathlib import Path
from typing import List, Dict
from pydantic import BaseModel
from config.settings import MAX_QUERY_LENGTH
from _services.mongo.client import MongoDbClient
from _documents.settings.schema import Setting

from utils.logger import logger


async def handle_data(doc, data): 
    if doc == 'contract':
        for x in data:
            if (
                product := await MongoDbClient().get_docs('product').find_one({'title': x['product']})
            ) is not None:
                x["product"] = product['_id']
    return data


async def filter_missing(name: str, keys: str, data: List[dict]):
    existing_keys = []
    for doc in await MongoDbClient().get_docs(name).find({
        '$or': [ { k: x[k] for k in keys } for x in data ]
    }).to_list(length=MAX_QUERY_LENGTH):
        existing_keys.append({ k: doc[k] for k in keys })
    return [x for x in data if { k: x[k] for k in keys } not in existing_keys]


async def load_dataset():
    document_schemas: Dict[str, BaseModel] = {
        # CODE HERE
        # "settings": Setting
    }
    data_path = f"{Path(__file__).parent.resolve()}/data/"

    document_initialized = []
    for name, schema in document_schemas.items():
        logger.info(f"load_dataset {name}")
        # await MongoDbClient().get_docs(name).delete_many({
        #     'created_at': {'$gte': datetime.utcnow() - timedelta(minutes=30)}
        # })
        try:
            f = open(f"{data_path}/{name}.json")
            data: List[dict] = await handle_data(name, json.load(f))
            should_load = False
            if (
                existing_data := await MongoDbClient().get_docs(name).find_one({})
            ) is None:
                should_load = True
            else:
                if name == 'settings':
                    data = await filter_missing(name, ['key'], data)
                    should_load = len(data) > 0
                # if name == 'billing_account':
                #     data = await filter_missing(name, ['provider', 'currency'], data)
                #     should_load = len(data) > 0
            if not should_load: continue
            logger.info(data)
            results = await MongoDbClient().get_docs(name).insert_many([
                { k: v for k, v in schema(**x).dict().items() if v is not None }
                for x in data
            ])

            document_initialized.append({
                "document": name, 
                "total": len(data), 
                "inserted": len(results.inserted_ids)
            })
        except Exception as e:
            logger.warn(f"load_dataset error: {e}")

    for x in document_initialized:
        logger.info(f"load_dataset {x['document']} installation : {x['inserted']} / {x['total']} records have been inserted.")
    
    return
