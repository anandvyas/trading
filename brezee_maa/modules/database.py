import duckdb
import json
import pandas as pd

from modules.utility import Utility

class Database():

    def __init__(self) -> None:
        self.u = Utility()
        self.conn = duckdb.connect("./db/orders.db",read_only=False)
        
        # create table if not exist  
        # type - call or put (because right is reserved keyword)
        # side - Buy or Sell
        query = """
            CREATE TABLE IF NOT EXISTS orders(
                order_id BIGINT NOT NULL PRIMARY KEY, 
                symbol VARCHAR,
                type VARCHAR,
                side VARCHAR,
                qty INTEGER,
                ltp DECIMAL,
                cltp DECIMAL,
                status BOOL,
                strategy_name VARCHAR)
        """
        self.conn.sql(query)

    def _saveOrders(self, strategy_name, orders: pd.DataFrame):
        self.u._set(strategy_name, val = orders.to_json())
        
    
    def _getOrders(self, strategy_name):
        val = self.u._get(strategy_name)
        val = {} if val == None else json.loads(val)
        return pd.DataFrame(val)

    