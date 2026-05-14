from io import BytesIO
from zipfile import ZipFile
import xml.etree.ElementTree as ET

import pandas as pd
import requests

from pj_stock_backend.core.config import settings


DART_CORP_CODE_URL = "https://opendart.fss.or.kr/api/corpCode.xml"


def build_dart_params() -> dict[str, str]:
    if not settings.dart_api_key:
        msg = "DART_API_KEY is not configured"
        raise ValueError(msg)

    return {"crtfc_key": settings.dart_api_key}


def fetch_corp_codes() -> pd.DataFrame:
    response = requests.get(DART_CORP_CODE_URL, params=build_dart_params(), timeout=30)
    response.raise_for_status()

    with ZipFile(BytesIO(response.content)) as zip_file:
        xml_name = zip_file.namelist()[0]
        xml_content = zip_file.read(xml_name)

    root = ET.fromstring(xml_content)

    rows = []
    for item in root.findall("list"):
        rows.append(
            {
                "corp_code": item.findtext("corp_code", default=""),
                "corp_name": item.findtext("corp_name", default=""),
                "stock_code": item.findtext("stock_code", default=""),
                "modify_date": item.findtext("modify_date", default=""),
            }
        )

    return pd.DataFrame(rows)
