import os
import json
import time
import logging
import datetime
import pandas as pd
from datetime import date, timedelta

logging.getLogger(__name__)

class Utility:

    def __init__(self) -> None:
        self.dataFolder = "static"  

    def _createPath(self, path):
        filepath = f"./{self.dataFolder}/{path}"
        if self._createDir(filepath):
            return filepath

    def _createDir(self, filepath):
        dirname = os.path.dirname(filepath)
        try:
            isExist = os.path.exists(dirname)
            if not isExist:
                os.makedirs(dirname)
                return True
            else:
                return True
        except Exception as e:
            logging.DEBUG(str(e))
            return False
    
    def _get(self, key:str):
        try:
            with open('./configs/settings.json', 'r+') as f:
                data = json.load(f)
                if key in data:
                    return data[key]
        except Exception as e:
            logging.error(f"{e}-{key} - key not found")
            return None

    def _set(self, key, val):
        with open('./configs/settings.json', 'r+') as f:
            data = json.load(f)
            data[key] = val
            f.seek(0)  
            json.dump(data, f, indent=4)
            f.truncate()
