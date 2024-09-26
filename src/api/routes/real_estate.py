import logging
import os

import requests
import xmltodict
from dotenv import load_dotenv
from fastapi import APIRouter

load_dotenv()
router = APIRouter()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logging.getLogger("urllib3").setLevel(logging.DEBUG)

koreaLandUrl = os.getenv('KOREA_LAND_API_URL')
ministryUrl = os.getenv('MINISTRY_OF_LAND_API_URL')
encodingKey = os.getenv('ENCODING_KEY')


# 국토교통부 아파트 실거래가 Open API를 활용한 부동산 데이터 지역별/날짜별 조회
@router.get("/ministry/{LAWD_CD}/{DEAL_YMD}")
def read_real_estate_data_from_ministry(LAWD_CD: str, DEAL_YMD: str):
    params = {
        'LAWD_CD': LAWD_CD,
        'DEAL_YMD': DEAL_YMD,
    }

    response = requests.get(ministryUrl + '/getRTMSDataSvcAptTrade' + f'?serviceKey={encodingKey}',
                            params=params)

    if response.status_code == 200:
        data_dict = xmltodict.parse(response.content)

        items = data_dict['response']['body']['items']['item']
        return items
    else:
        return {"error": "Failed to fetch data"}


# 한국부동산원 월별 아파트 평균매매가격 동향 Open API를 활용한 부동산 데이터 지역별/날짜별 조회
@router.get("/korea_land")
def read_real_estate_data_from_korea_land(region: str, date: str):
    params = {
        'page': 1,
        'perPage': 10,
    }

    response = requests.get(koreaLandUrl + '//15069826/v1/uddi:754c056e-8dea-4201-8a61-88e56da67e83', params=params)

    if response.status_code == 200:
        data_dict = xmltodict.parse(response.content)

        items = data_dict['response']['body']['items']['item']
        return items
    else:
        return {"error": "Failed to fetch data"}
