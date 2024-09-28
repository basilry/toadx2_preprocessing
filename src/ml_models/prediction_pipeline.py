import pandas as pd
import numpy as np

np.float_ = np.float64
from prophet import Prophet
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from src.database.models.kb_real_estate_data_hub import PropertyPriceData, Prediction
from src.database.database import SessionLocal


# 기준 시점의 가격을 DB에서 가져오는 함수 (2022-01-10 기준)
def get_basis_price(session: Session, region_id: int, price_type: str):
    """
    기준 시점(2022-01-10)의 지역별 매매/전세 가격을 DB에서 가져오는 함수.
    region_id: 지역 ID
    price_type: 매매 또는 전세
    """
    BASIS_DATE_WEEKLY = datetime(2022, 1, 10)  # 기준 날짜: 2022-01-10

    # 기준 시점의 매매/전세 가격을 가져옴
    basis_data = session.query(PropertyPriceData).filter_by(
        region_id=region_id,
        price_type=price_type,
        date=BASIS_DATE_WEEKLY
    ).first()

    # 기준 시점 데이터가 존재하지 않으면 예외 처리
    if not basis_data or not basis_data.avg_price:
        raise ValueError(f"기준 시점 데이터가 없습니다: 지역 {region_id}, 가격 유형 {price_type}, 날짜 {BASIS_DATE_WEEKLY}")

    return basis_data.avg_price


# 예측 결과를 저장하는 함수
def store_prediction(session: Session, region_id: int, date: datetime, price_type: str, predicted_index: float = None):
    # region_id가 numpy.int64일 경우 Python의 int로 변환
    region_id = int(region_id)

    # 기준 시점의 가격을 DB에서 가져옴 (2022-01-10)
    try:
        basis_price = get_basis_price(session, region_id, price_type)
    except ValueError as e:
        print(f"기준 시점 가격을 가져오지 못했습니다: {e}")
        return

    # 예측된 지수를 기준으로 실제 가격 계산 (지수 -> 실제 가격 변환)
    predicted_price = None
    if predicted_index is not None:
        predicted_price = (predicted_index / 100) * basis_price

    # 기존 예측 데이터 확인
    existing_prediction = session.query(Prediction).filter_by(
        region_id=region_id,
        date=date,
        price_type=price_type
    ).first()

    if not existing_prediction:
        # 새 예측 데이터 추가
        prediction = Prediction(
            region_id=region_id,
            date=date,
            price_type=price_type,
            predicted_index=predicted_index,  # 예측된 가격 지수
            predicted_price=predicted_price  # 계산된 실제 가격
        )
        session.add(prediction)
        session.commit()
        print(f"Prediction inserted for region {region_id} on {date}.")
    else:
        print(f"Prediction already exists for region {region_id} on {date} - Skipping.")


# Prophet 모델을 사용하여 미래 데이터 예측
def predict_future_property_prices(session: Session, price_type: str):
    # DB에서 주간 데이터를 가져오기
    property_data = session.query(PropertyPriceData).filter_by(price_type=price_type).all()

    if not property_data:
        print(f"No data found for {price_type}.")
        return

    # 데이터를 Pandas DataFrame으로 변환
    data = [{'ds': pd.to_datetime(item.date), 'y': item.index_value, 'region_id': item.region_id} for item in
            property_data]
    df = pd.DataFrame(data)

    # 오늘 날짜 설정
    today = datetime.today().date()

    # 지역별로 데이터를 그룹화하고 예측 수행
    regions = df['region_id'].unique()
    for region_id in regions:
        region_data = df[df['region_id'] == region_id]

        if region_data.empty:
            continue

        # 2020-01-01, 2021-01-01에서 부동산 가격이 급격히 변화하는 지점을 changepoints로 설정
        changepoints = ['2019-01-01', '2020-01-01', '2021-01-01']

        # Prophet 모델 학습
        region_data['cap'] = region_data['y'].max() * 1.5
        model = Prophet(growth='logistic', changepoints=changepoints, changepoint_prior_scale=0.1)
        model.fit(region_data[['ds', 'y', 'cap']])

        # 12개월(주단위로) 미래 예측
        future = model.make_future_dataframe(periods=156, freq='W')
        future['cap'] = region_data['y'].max() * 1.5
        forecast = model.predict(future)

        # 예측 값을 스무딩 처리 (Moving Average 적용)
        forecast['yhat_smooth'] = forecast['yhat'].rolling(window=3, min_periods=1).mean()

        # 미래 1년치 데이터를 저장
        for _, row in forecast.iterrows():
            prediction_date = row['ds'].date()

            # 오늘 이후의 데이터만 처리 (과거 데이터 제외)
            if prediction_date > today:
                predicted_value = row['yhat_smooth']  # 스무딩된 값을 사용

                # 예측값 저장 (미래 데이터만 저장)
                store_prediction(session, region_id, prediction_date, price_type, predicted_index=predicted_value)

    print(f"Future predictions for {price_type} have been successfully generated and stored.")


# 전체 예측 프로세스를 실행하는 함수
def run_prediction_pipeline():
    session = SessionLocal()

    # 1. 매매 예측
    predict_future_property_prices(session, "매매")

    # 2. 전세 예측
    predict_future_property_prices(session, "전세")

    print("All predictions have been processed.")


if __name__ == "__main__":
    run_prediction_pipeline()
