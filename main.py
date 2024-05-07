"""load from frankfurter api"""
from collections import defaultdict
from datetime import date, datetime
from fastapi import FastAPI, Request, Response
import requests
import pandas as pd
import numpy as np

app = FastAPI()


def df_to_xlb(df: pd.DataFrame):
    return df.to_dict(orient="dict")


def get_fx(to: str, start_date: date, end_date: date):
    base_url = "https://api.frankfurter.app"
    url = f"{base_url}/{start_date:%Y-%m-%d}..{end_date:%Y-%m-%d}?to={to.upper()}"
    resp = requests.get(url, timeout=4)

    # the frankfurter API will return a 200 if the
    # request was successful
    if resp.status_code != 200:
        raise Exception(f"unable to load data for {to}, {start_date}, {end_date}")
    else:
        # convert our response to a dictionary
        data = resp.json()

    # check that rates is available in the dictionary
    rates = data.get("rates", None)

    # the rates key contains the FX timeseies
    # if it's not available it means the request
    # was a success, but there is no data for the time period
    if rates is None:
        raise Exception(f"no data for EUR/{to}, {start_date}, {end_date}")

    # convert the data into a shape
    # compatible with pandas
    out = defaultdict(list)
    for d in rates.keys():
        out["date"].append(d)
        out["value"].append(rates[d].get(to, np.nan))

    return pd.DataFrame(out)


@app.get("/ecbfx/xlba")
async def data_get(request: Request):
    return get_fx("USD", date(2022, 1, 1), date(2023, 1, 1))


@app.post("/ecbfx/xlba")
async def data_post(request: Request, response: Response):
    """process the Excel Bing request

    Notes
    -----

    Payload looks like:
    `
    {
        "data":{
            "namespace":"FF.FX",
            "payload":{
                "to":[
                    {
                    "value":"test"
                    }
                ],
                "start_date":[
                    {
                    "value":"2023-12-27T16:51:36.626Z"
                    }
                ],
                "end_date":[
                    {
                    "value":"2023-12-27T16:51:36.626Z"
                    }
                ]
            }
        }
    }
    `

    """
    # at this point you should check that your token is valid,
    # the token is available in request.headers: "x-xlb-api-key"
    xlb_request = await request.json()

    data = xlb_request.get("data", {})
    namespace = data.get("namespace", None)

    if namespace != "ECB.FX":
        response.status_code = 400
        return {"error": {"message": "invalid namespace"}}

    # parse relevant keys
    payload = data.get("payload", None)
    to = payload.get("to", None)
    start_date = payload.get("start_date", None)
    end_date = payload.get("end_date", None)

    if to is None or start_date is None or end_date is None:
        response.status_code = 400
        return {"error": {"message": "invalid input"}}

    try:
        start_date = datetime.strptime(start_date[0]["value"], "%Y-%m-%d %H:%M:%S")
        end_date = datetime.strptime(end_date[0]["value"], "%Y-%m-%d %H:%M:%S")
        data = get_fx(to[0]["value"], start_date.date(), end_date.date())

    except Exception as e:
        response.status_code = 400
        return {"error": {"message": "unable to process", "detail": f"{e}"}}

@app.post("/echo/xlba")
async def data_post(request: Request, response: Response):
    from datetime import datetime
    return {"data": {"A": {0: datetime.now()}}}
