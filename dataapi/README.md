We divide the entire program into four major sections. 

### DataAPI
--- 

DataAPI is primarily responsible for providing data required by strategies such as historical data, market live tick, and socket connection for market feed.

This DataAPI will not store any type of data in the database, because most vendors now provide historical data, and if we require any historical for backtesting, we can create a separate module for backtesting and pull the data from this module and store it in the backtesting module itself.

Some of the command functions that we require 
```python
# Last trading price (LTP): It will provide the last trading price of the symbol, which includes all symbols such as stock, option, and future.

def _getltp(symbol)
```

```python
# Download historical data: A function that provides historical data for all types of symbols such as stocks, options, and futures is required. 

def historical_data(symbol, start="", end="")

```

### Strategies
---

### Broker
---

### Backtesting / Paper trading
---


### Not decided yet 
---
- Get all the index
- get current, next and far expiry 
- get all the expiries 

