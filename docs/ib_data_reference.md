# ib-insync Market Data Reference
**Quick Reference for Real-Time & Historical Data**

## ⚠️ CRITICAL RULE

**USE STREAMING, NOT POLLING**

❌ **NEVER DO THIS:**
```python
while True:
    bars = ib.reqHistoricalData(...)  # DON'T POLL!
    time.sleep(5)
```

✅ **ALWAYS DO THIS:**
```python
# For ticks
ticker = ib.reqMktData(contract)
ticker.updateEvent += process_tick

# For bars  
bars = ib.reqRealTimeBars(contract, 5, 'TRADES', False)
bars.updateEvent += process_bar
```

---

## Real-Time Streaming Data

### Basic Ticker (Streaming)
```python
ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)

contract = Stock('AAPL', 'SMART', 'USD')
contract = ib.qualifyContracts(contract)[0]

# Start streaming
ticker = ib.reqMktData(contract, '', False, False)

# Wait for data
ib.sleep(2)

print(f"Bid: {ticker.bid}")
print(f"Ask: {ticker.ask}")
print(f"Last: {ticker.last}")
print(f"Volume: {ticker.volume}")
```

### With Event Handler
```python
def on_ticker_update(ticker):
    print(f"{ticker.contract.symbol}: ${ticker.last:.2f}")

ticker = ib.reqMktData(contract)
ticker.updateEvent += on_ticker_update
```

### Generic Ticks (Extra Data)
```python
# Request additional data
ticker = ib.reqMktData(
    contract,
    genericTickList='233,236',  # Volume, shortable shares
    snapshot=False
)

ib.sleep(2)
print(f"VWAP: {ticker.vwap}")
print(f"RT Volume: {ticker.rtVolume}")
```

### Generic Tick IDs
```
100 - Option volume
101 - Option open interest  
104 - Historical volatility
106 - Implied volatility
165 - 52-week high/low
221 - Mark price
233 - Last, volume, VWAP
236 - Shortable shares
258 - Fundamental ratios
```

### Cancel Streaming
```python
ib.cancelMktData(contract)
```

---

## Real-Time Bars (5-Second Updates)

```python
bars = ib.reqRealTimeBars(
    contract,
    barSize=5,              # Always 5 seconds
    whatToShow='TRADES',    # TRADES, MIDPOINT, BID, ASK
    useRTH=False
)

def on_bar_update(bars, hasNewBar):
    if hasNewBar:
        bar = bars[-1]
        print(f"{bar.date} O:{bar.open} H:{bar.high} L:{bar.low} C:{bar.close} V:{bar.volume}")

bars.updateEvent += on_bar_update

# Cancel when done
ib.cancelRealTimeBars(bars)
```

---

## Historical Data (Backtesting Only)

### Basic Historical Request
```python
bars = ib.reqHistoricalData(
    contract,
    endDateTime='',          # '' = now
    durationStr='30 D',      # 30 days
    barSizeSetting='1 hour',
    whatToShow='TRADES',
    useRTH=True              # Regular hours only
)

# Convert to pandas
df = util.df(bars)
print(df.head())
```

### Duration Options
```
'60 S'  - 60 seconds
'1 D'   - 1 day
'2 W'   - 2 weeks
'6 M'   - 6 months
'1 Y'   - 1 year
```

### Bar Sizes
```
'1 secs', '5 secs', '15 secs', '30 secs'
'1 min', '5 mins', '15 mins', '30 mins'
'1 hour', '4 hours'
'1 day', '1 week', '1 month'
```

### What to Show
```
'TRADES'    - Actual trades (default)
'MIDPOINT'  - Bid/ask midpoint
'BID'       - Bid prices
'ASK'       - Ask prices
```

### Keep Historical Updated (Live)
```python
bars = ib.reqHistoricalData(
    contract,
    endDateTime='',
    durationStr='1 D',
    barSizeSetting='1 min',
    whatToShow='TRADES',
    useRTH=True,
    keepUpToDate=True  # ← Auto-update!
)

bars.updateEvent += lambda bars, hasNewBar: print(f"Updated: {hasNewBar}")
```

---

## Tick-by-Tick Data

```python
ticker = ib.reqTickByTickData(
    contract,
    tickType='AllLast',  # 'Last', 'BidAsk', 'AllLast', 'MidPoint'
    numberOfTicks=0,
    ignoreSize=False
)

def on_tick(ticker):
    if ticker.tickByTicks:
        tick = ticker.tickByTicks[-1]
        print(f"Tick: {tick.time} {tick.price} x {tick.size}")

ticker.updateEvent += on_tick
```

---

## Market Depth (Level II)

```python
ticker = ib.reqMktDepth(
    contract,
    numRows=10,
    isSmartDepth=False
)

ib.sleep(2)

print("Bids:")
for bid in ticker.domBids:
    print(f"  {bid.price} x {bid.size}")

print("Asks:")
for ask in ticker.domAsks:
    print(f"  {ask.price} x {ask.size}")

# Cancel
ib.cancelMktDepth(contract)
```

---

## Multiple Tickers Pattern

```python
contracts = [
    Stock('AAPL', 'SMART', 'USD'),
    Stock('GOOGL', 'SMART', 'USD'),
    Stock('MSFT', 'SMART', 'USD')
]

contracts = ib.qualifyContracts(*contracts)

def on_pending_tickers(tickers):
    for ticker in tickers:
        print(f"{ticker.contract.symbol}: ${ticker.marketPrice():.2f}")

ib.pendingTickersEvent += on_pending_tickers

# Subscribe to all
for contract in contracts:
    ib.reqMktData(contract)

ib.run()  # Run event loop
```

---

## Market Data Type

```python
# 1 = Live (subscription required)
# 2 = Frozen (snapshot)
# 3 = Delayed (free, 15-min delay)
# 4 = Delayed-Frozen

ib.reqMarketDataType(3)  # Use delayed data (free)
```

---

## Common Patterns

### Price Alert System
```python
def price_alert(ticker, target_price, above=True):
    """Alert when price crosses threshold"""
    def check_price(ticker):
        if not ticker.last or ticker.last != ticker.last:
            return
        
        if above and ticker.last >= target_price:
            print(f"ALERT: {ticker.contract.symbol} above ${target_price}")
            ticker.updateEvent -= check_price  # Unsubscribe
        elif not above and ticker.last <= target_price:
            print(f"ALERT: {ticker.contract.symbol} below ${target_price}")
            ticker.updateEvent -= check_price
    
    ticker.updateEvent += check_price

# Usage
ticker = ib.reqMktData(contract)
price_alert(ticker, 180.0, above=True)
```

### Moving Average Calculator
```python
class MovingAverage:
    def __init__(self, period=20):
        self.period = period
        self.prices = []
    
    def update(self, price):
        self.prices.append(price)
        if len(self.prices) > self.period:
            self.prices.pop(0)
    
    def value(self):
        return sum(self.prices) / len(self.prices) if self.prices else None

ma20 = MovingAverage(20)

def on_bar(bars, hasNewBar):
    if hasNewBar:
        bar = bars[-1]
        ma20.update(bar.close)
        if ma20.value():
            print(f"Price: {bar.close:.2f} | MA20: {ma20.value():.2f}")

bars = ib.reqRealTimeBars(contract, 5, 'TRADES', False)
bars.updateEvent += on_bar
```

### OHLC Tracker
```python
class OHLCTracker:
    def __init__(self):
        self.open = None
        self.high = None
        self.low = None
        self.close = None
    
    def update(self, price):
        if self.open is None:
            self.open = price
        
        if self.high is None or price > self.high:
            self.high = price
        
        if self.low is None or price < self.low:
            self.low = price
        
        self.close = price
    
    def reset(self):
        self.open = self.high = self.low = self.close = None

tracker = OHLCTracker()

def on_tick(ticker):
    if ticker.last:
        tracker.update(ticker.last)
        print(f"O:{tracker.open} H:{tracker.high} L:{tracker.low} C:{tracker.close}")

ticker = ib.reqMktData(contract)
ticker.updateEvent += on_tick
```

---

## Best Practices

✅ Use reqRealTimeBars for live bar data
✅ Use reqMktData for tick data
✅ Use events, not polling loops
✅ Cancel subscriptions when done
✅ Use reqMarketDataType(3) for free delayed data
✅ Always use ib.sleep() not time.sleep()

❌ Don't poll reqHistoricalData repeatedly
❌ Don't subscribe to 100+ tickers simultaneously
❌ Don't forget to cancel subscriptions
❌ Don't use time.sleep() - blocks event loop
❌ Don't use waitOnUpdate() for tick collection

---

## Troubleshooting

**No data received:**
- Check market hours
- Verify data subscription
- Use reqMarketDataType(3) for delayed

**Missing ticks:**
- Use events, not waitOnUpdate()
- Don't process in tight loops

**Rate limiting:**
- IB limits: 45 req/sec, 60 market data
- ib-insync throttles automatically