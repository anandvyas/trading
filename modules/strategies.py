import pandas as pd
import pandas_ta as ta
import numpy as np

class Strategies:

    def __init__(self) -> None:
        pass

    def _bband(df, short = 9, long = 21):

        tdf = df.copy()
        tdf['SMA'] = tdf.close.rolling(20).mean()
        tdf['stddev'] = tdf.close.rolling(20).std()

        tdf.loc[:,'upper'] = tdf['SMA'] + 2* tdf['stddev']
        tdf.loc[:,'lower'] = tdf['SMA'] - 2* tdf['stddev']

        tdf.loc[:,'trail_stoploss'] = tdf['close'] - (tdf['close'] * 3/100)

    def _macdCrossover(df, short = 12, long = 26):

        tdf = df.copy()
        tdf['short_ema'] = tdf.close.ewm(span=short, adjust = False).mean()
        tdf['long_ema'] = tdf.close.ewm(span=long, adjust = False).mean()
        tdf['macd'] = tdf['short_ema'] - tdf['long_ema']
        tdf['signal'] = tdf['macd'].ewm(span=9).mean()

        return np.where((tdf['macd'] > tdf['signal']), True, False)


    def _crossover(df, short = 9, long = 21):

        tdf = df

        tdf['short'] = tdf.close.ewm(span=short).mean()
        tdf['long'] = tdf.close.ewm(span=long).mean()

        return np.where((tdf['short'] > tdf['long']), True, False)