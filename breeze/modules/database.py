import datetime
from datetime import date, timedelta
import pandas as pd
import influxdb_client, os, time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

token = os.environ.get("INFLUXDB_TOKEN")
org = os.environ.get("INFLUXDB_ORG")
url = os.environ.get("INFLUXDB_URL")
bucket = os.environ.get("INFLUXDB_BUCKET")

class Database():

    def __init__(self) -> None:
        self.client = influxdb_client.InfluxDBClient(url=url, token=token, org=org)

    def _saveStockData(self, db, df):
        # df["datetime"] = df["datetime"].apply(lambda x: datetime.datetime.strptime(f"{x}","%Y-%m-%d %H:%M:%S").utcnow().isoformat('T'))
        # headers = ["close","datetime","exchange_code","high","low","open","stock_code","volume"]
        # df.set_index('datetime', inplace=True)

        # write_api = self.client.write_api(write_options=SYNCHRONOUS)
        # write_api.write(bucket=bucket, record=df, data_frame_measurement_name=db,data_frame_tag_columns=["exchange_code","stock_code"])
        pass






