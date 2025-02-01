# Fyers API

### Order place
---
- symbol*	string	Eg: NSE:SBIN-EQ
- qty*	int	The quantity should be in multiples of lot size for derivatives.
- type*	int	
    - 1 => Limit Order
    - 2 => Market Order
    - 3 => Stop Order (SL-M)
    - 4 => Stoplimit Order (SL-L)
  - side*	int	
    - 1 => Buy
    - -1 => Sell
  - productType*	string	
    - CNC => For equity only
    - INTRADAY => Applicable for all segments.
    - MARGIN => Applicable only for derivatives
    - CO => Cover Order
    - BO => Bracket Order
  - limitPrice*	float	Default => 0
  - stopPrice*	float	Default => 0
  - disclosedQty*	int	Default => 0
Allowed only for Equity
validity*	string	IOC => Immediate or Cancel
DAY => Valid till the end of the day
offlineOrder*	string	False => When market is open
True => When placing AMO order
stopLoss*	float	Default => 0
Provide valid price for CO and BO orders
takeProfit*	float	Default => 0
Provide valid price for BO orders