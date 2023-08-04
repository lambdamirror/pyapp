import abc
import csv
import io
import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import List

import pandas as pd
from borb.pdf.canvas.font.simple_font.true_type_font import TrueTypeFont

from _services.s3.manager import s3_manager
from utils.helper import split_data
from babel import numbers

class XLSXBuilder():

    def __init__(self, headers:List[str] = [], data: List[dict] = []) -> None:
        self.headers = headers
        self.rows = self._handle_data(data)

    @abc.abstractmethod
    def _handle_data(self, data):
        return pd.DataFrame(data, columns=self.headers)

    def save_to_local(self, file_name):
        with open(file_name, 'w') as csvfile: 
            # creating a csv writer object 
            csvwriter = csv.writer(csvfile) 
                
            # writing the header 
            csvwriter.writerow(self.headers) 
                
            # writing the data rows 
            csvwriter.writerows(self.rows.values.tolist())
    
    def export_to_s3(self, file_name):
        with io.BytesIO() as output:
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                self.rows.to_excel(writer, index=False)
            data = output.getvalue()

            return {
                "url": s3_manager.get_client().put_object(f"{file_name}.xlsx", data),
                "file_name": f"{file_name.split('/')[-1]}.xlsx"
            }


class CSVBuilder():
    headers = []
    prefix = ''

    def __init__(self, bill_data: dict, name: str, data: List[dict]) -> None:
        self.bill_id = str(bill_data['id'])[-5:]
        self.bill_data = bill_data
        self.name = name if name is not None else ""
        self.rows = self._handle_data(data)

    @abc.abstractmethod
    def _handle_data(self, data) -> pd.DataFrame:
        pass

    def save_to_local(self):
        with open('output.csv', 'w') as csvfile: 
            # creating a csv writer object 
            csvwriter = csv.writer(csvfile) 
                
            # writing the header 
            csvwriter.writerow(self.headers) 
                
            # writing the data rows 
            csvwriter.writerows(self.rows.values.tolist())
    
    def export_to_s3(self):
        str_buffer = io.StringIO()
        csvwriter = csv.writer(str_buffer) 
        # writing the header 
        csvwriter.writerow(self.headers) 
    
        # writing the data rows 
        csvwriter.writerows(self.rows.values.tolist())

        str_buffer.seek(0)
        str_data = str_buffer.read().encode('utf8')
    
        bytes_buffer = io.BytesIO(str_data)
        bytes_buffer.seek(0)
        return s3_manager.get_client().upload_object(bytes_buffer, f'_bill/[{self.bill_id[-5:]}]_{self.prefix}_{self.name.lower()}.csv')


class PDFBuilder():

    @staticmethod
    def build_font_from_file(filename: str):
        with open(f"{Path(__file__).parent}/fonts/{filename}.ttf", "rb") as ffh:
            font_file_bytes = ffh.read()
            return TrueTypeFont.true_type_font_from_file(font_file_bytes)
        
    @staticmethod
    def format_currency(number: float, currency: str):
        if currency == 'VND':
            return f"VND{numbers.format_number(number, locale='en')}"
        return numbers.format_currency(number, currency, locale='en')