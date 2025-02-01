import os
import json
import logging
import requests
from os.path import join, dirname
from dotenv import load_dotenv

# Fyers API
from fyers_api import fyersModel
from fyers_api import accessToken

# Trading packages
import pandas as pd
import pandas_ta as ta
import matplotlib.pyplot as plt

# Read env values
dotenv_path = join(dirname(__file__), '../.env')
load_dotenv(dotenv_path)

class utils:

    def __init__(self) -> None:
        pass

    def _getGraph(df):

        plt.figure(figsize=(24,10))
        plt.plot(df[['close','EMA_20', 'upper', 'lower']])
        plt.scatter(df.index[df.entries], df[df.entries].close, marker='^', color='g')
        plt.scatter(df.index[df.exits], df[df.exits].close, marker='>', color='r')
        plt.fill_between(df.index, df['upper'], df['lower'], color='grey', alpha=0.3)
        plt.legend(['close', 'EMA_20', 'upper', 'lower'])
        plt.show()

    def heikin_ashi(df):
        heikin_ashi_df = pd.DataFrame(index=df.index.values, columns=['open', 'high', 'low', 'close'])
        heikin_ashi_df['close'] = (df['open'] + df['high'] + df['low'] + df['close']) / 4
        heikin_ashi_df['open'] = (df['open'].shift(1) + df['close'].shift(1)) / 2
        heikin_ashi_df['high'] = heikin_ashi_df.loc[:, ['open', 'close']].join(df['high']).max(axis=1)
        heikin_ashi_df['low'] = heikin_ashi_df.loc[:, ['open', 'close']].join(df['low']).min(axis=1)
        return heikin_ashi_df

    def _addEntryExit(df, pp = 2, lp = 2):

        df.loc[:, "entries"] = False
        df.loc[:, "exits"] = False

        profit_percentage = pp / 100
        loss_percentage = lp / 100

        profit_target = 0
        loss_target = 0
        open_pos = False

        for ind, row in df.iterrows():
            if (df['entries_pos'][ind] and open_pos == False):
                open_pos = True
                df.loc[ind, 'entries'] = True
                profit_target = df['close'][ind] + df['close'][ind] * profit_percentage 
                loss_target = df['close'][ind] - df['close'][ind] * loss_percentage     
                # logging.info(f"Entry - time - {ind} close: {df['close'][ind]} profit: {profit_target} loss: {loss_target}")
                
            if (open_pos == True):
                if (df['close'][ind] > loss_target and df['close'][ind] <  profit_target):
                    None
                elif (df['close'][ind] > profit_target):
                    profit_target = df['close'][ind] + df['close'][ind] * profit_percentage 
                    loss_target = df['close'][ind] - df['close'][ind] * loss_percentage  
                    # logging.info(f"Change - time - {ind} close: {df['close'][ind]} profit: {profit_target} loss: {loss_target}")
                elif (df['close'][ind] < loss_target):
                    df.loc[ind, 'exits'] = True
                    open_pos = False
                    # logging.info(f"Exit - time - {ind} close: {df['close'][ind]} profit: {profit_target} loss: {loss_target}")

        return df
