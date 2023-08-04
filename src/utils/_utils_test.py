from decimal import Decimal
from os import listdir
from os.path import isfile, join
from pathlib import Path
from typing import List

import pandas as pd
import pytest
from borb.pdf import Document, HexColor, Page, Paragraph, SingleColumnLayout
from borb.pdf.canvas.font.simple_font.true_type_font import TrueTypeFont
from bson import ObjectId

from config.conftest import *
from utils.logger import logger


@pytest.mark.asyncio 
def test_fonts():
    text = "a, ă, â, b, c, d, đ, e, ê, g, h, i, k l, m, n, o, ô, ơ, p, q, r, s, t, u, ư, v, x, y".split(", ")
    fonts_path = f"{Path(__file__).parent}/fonts"
    files = [f for f in listdir(fonts_path) if isfile(join(fonts_path, f))]
    pdf = Document()
    page = Page()
    pdf.add_page(page)
    layout = SingleColumnLayout(page)

    for file in sorted(files):
        # font_path: Path = f"{Path(__file__).parent}/{file}.ttf"
        
        with open(f"{fonts_path}/{file}", "rb") as ffh:
            font_file_bytes = ffh.read()
            custom_font = TrueTypeFont.true_type_font_from_file(font_file_bytes)
            try: 
                for c in text:               
                    layout.add(Paragraph(c, font=custom_font, font_size= Decimal(16), font_color=HexColor('F9D342')))
            except Exception as e:
                logger.error(file)



    

