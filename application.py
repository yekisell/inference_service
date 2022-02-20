import logging
import pickle
from typing import Optional

from pandas.core.frame import DataFrame as dataFrame
import uvicorn
from fastapi import FastAPI, HTTPException
import xgboost as xgb
from fastapi.responses import PlainTextResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.datamodel.response import RossmannResponse
from src.datamodel.request import RossmannRequest
from src.processing.validator import sample_validation
import src.processing.transformer as transform

logger = logging.getLogger(__name__)
maps: Optional[list[dict]] = None
store_data: Optional[dataFrame] = None
model: Optional[xgb.sklearn.XGBRegressor] = None

app = FastAPI()


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return PlainTextResponse(str(exc.detail), status_code=exc.status_code)


def load_from_archives(path: str):
    with open(path, "rb") as f:
        return pickle.load(f)


@app.on_event("startup")
def load_savings():
    maps_path = "pickle_packages/encoding_maps"
    store_path = "pickle_packages/stores_data"
    model_path = "pickle_packages/xgb_model_1500"
    try:
        maps_l = load_from_archives(maps_path)
        store_data_l = load_from_archives(store_path)
        model_l = load_from_archives(model_path)
    except FileNotFoundError as err:
        print("Something got wrong!")
        logger.error(err)
        return
    global store_data, maps, model
    maps = maps_l
    store_data = store_data_l
    model = model_l


@app.post("/predict", response_model=list[RossmannResponse], status_code=200)
def prediction(requests: list[RossmannRequest]):
    for request in requests:
        is_valid, mes = sample_validation(request)
        if not is_valid:
            raise HTTPException(status_code=423, detail=mes)

        if request.Open == 0:
            return RossmannResponse(Id=request.Id, Sales=0)

    requests_df = transform.transform_to_df(requests)
    ids_, requests_df = requests_df["Id"], requests_df.drop("Id", axis=1)

    predicted_sales = model.predict(requests_df)

    return [
        RossmannResponse(Id=id_, Sales=predicted_sale)
        for id_, predicted_sale in zip(ids_, predicted_sales)
    ]


if __name__ == "__main__":
    uvicorn.run("application:app")
