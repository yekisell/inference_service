import logging
import pickle
from typing import Optional

import pandas as pd
import uvicorn
from fastapi import FastAPI, HTTPException
import xgboost as xgb
from fastapi.responses import PlainTextResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from datetime import datetime

from pydantic import BaseModel

logger = logging.getLogger(__name__)
maps: Optional[list[dict]] = None
store_data: Optional[pd.core.frame.DataFrame] = None
model: Optional[xgb.sklearn.XGBRegressor] = None
is_ok: bool = False

app = FastAPI()


class RossmannRequest(BaseModel):
    Id: int = 0
    Store: int = 1
    DayOfWeek: int = 1
    Date: str = '2015-08-01'
    Open: bool = 1
    Promo: bool = 0
    StateHoliday: str = '0'
    SchoolHoliday: bool = 0


class RossmannResponse(BaseModel):
    Id: int
    Sales: float


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return PlainTextResponse(str(exc.detail), status_code=exc.status_code)


def sample_validation(sample: RossmannRequest) -> tuple[bool, str]:
    try:
        datetime.strptime(sample.Date, '%Y-%m-%d')
    except ValueError:
        return False, "Invalid Date! Print date in format YYYY-MM-DD"
    try:
        if sample.Store < 1 or sample.Store > 1115:
            raise ValueError('Store must be >=1 and <=1115')
        if sample.DayOfWeek < 1 or sample.DayOfWeek > 7:
            raise ValueError('DayOfWeek must be >=1 and <=7')
        if sample.Open not in [0, 1]:
            raise ValueError('Open must be either 0 or 1')
        if sample.Promo not in [0, 1]:
            raise ValueError('Promo must be either 0 or 1')
        if sample.SchoolHoliday not in [0, 1]:
            raise ValueError('SchoolHoliday must be either 0 or 1')
        if sample.StateHoliday not in ['0', 'a', 'b', 'c']:
            raise ValueError("StateHoliday must be in ['0', 'a', 'b', 'c']")
        return True, ""
    except ValueError as error:
        return False, str(error)


def transform_to_df(requests: list[RossmannRequest]):
    sam = [request.dict() for request in requests]
    df = pd.DataFrame(sam)

    df[['Promo', 'SchoolHoliday']] = df[['Promo', 'SchoolHoliday']].astype('object')
    df.drop(['Open'], axis=1, inplace=True)

    # New features
    df['Date'] = pd.to_datetime(df['Date'])
    df['Year'] = df.Date.dt.year
    df['Month'] = df.Date.dt.month
    df['DayOfMonth'] = df.Date.dt.day
    df['WeekOfYear'] = df.Date.dt.isocalendar().week
    df.drop('Date', axis=1, inplace=True)

    # Merging
    df_merged = df.merge(store_data, how='inner', on='Store')
    df_merged['WeekOfYear'] = df_merged['WeekOfYear'].astype('int')

    # Again some features
    df_merged['Current-OpenComp'] = 12 * (df_merged['Year'] - df_merged['CompetitionOpenSinceYear']) \
                                    + (df_merged['Month'] - df_merged['CompetitionOpenSinceMonth'])
    df_merged['Current-OpenPromo'] = 12 * (df_merged['Year'] - df_merged['Promo2SinceYear']) \
                                     + (df_merged['Month'] - df_merged['Promo2SinceWeek'] * 12 / 52)

    # Encoding
    for i, col in enumerate(df_merged.loc[:, df_merged.dtypes == 'object']):
        df_merged[col].replace(maps[i], inplace=True)

    return df_merged


def load_from_archives(path: str):
    with open(path, "rb") as f:
        return pickle.load(f)


@app.on_event("startup")
def load_savings():
    maps_path = 'pickle_packages/encoding_maps'
    store_path = 'pickle_packages/stores_data'
    model_path = 'pickle_packages/xgb_model_1500'
    try:
        maps_l = load_from_archives(maps_path)
        store_data_l = load_from_archives(store_path)
        model_l = load_from_archives(model_path)
    except FileNotFoundError as err:
        print('Something got wrong!')
        logger.error(err)
        return
    global store_data, maps, model, is_ok
    maps = maps_l
    store_data = store_data_l
    model = model_l
    is_ok = True


@app.post("/predict", response_model=list[RossmannResponse], status_code=200)
def prediction(requests: list[RossmannRequest]):
    for request in requests:
        is_valid, mes = sample_validation(request)
        if not is_valid:
            raise HTTPException(status_code=423, detail=mes)

        if request.Open == 0:
            return RossmannResponse(Id=request.Id, Sales=0)

    requests_df = transform_to_df(requests)
    ids_, requests_df = requests_df['Id'], requests_df.drop('Id', axis=1)

    predicted_sales = model.predict(requests_df)

    return [
        RossmannResponse(Id=id_, Sales=predicted_sale)
        for id_, predicted_sale in zip(ids_, predicted_sales)
    ]


if __name__ == "__main__":
    uvicorn.run("application:app")
