# Jupyter Notebooks Guide

This guide provides an overview of the interactive Jupyter notebooks available for learning and exploring ib_insync functionality. These notebooks demonstrate how to work with live data from within a Jupyter environment.

## Setup for Jupyter Notebooks

Before using these notebooks, you need to set up the event loop for Jupyter compatibility:

```python
from ib_insync import *

# Enable nested event loops for Jupyter
util.startLoop()

# Connect to IB Gateway or TWS
ib = IB()
ib.connect('127.0.0.1', 7497, clientId=10)
```

## Available Notebooks

### 1. Basics

**Link**: [basics.ipynb](https://nbviewer.jupyter.org/github/erdewit/ib_insync/tree/master/notebooks/basics.ipynb)

**Topics Covered**:
- Package overview and exported components (90+ classes and utilities)
- Connection setup and initialization
- State management and synchronized account access
- Contract specification approaches
- Difference between request methods vs. state access
- Logging configuration and debugging
- Clean disconnection procedures

**Key Concepts**:
- The `IB` class as the main interface
- Methods like `ib.positions()`, `ib.trades()`, `ib.accountValues()`
- Contract types: `Stock()`, `Forex()`, `Future()`, `Bond()`
- Performance comparison: state methods (~9μs) vs request methods (~32.7ms)

**Example Usage**:
```python
from ib_insync import *

util.startLoop()
ib = IB()
ib.connect('127.0.0.1', 7497, clientId=10)

# Get current positions
positions = ib.positions()
for pos in positions:
    print(f"{pos.contract.symbol}: {pos.position}")

# Create and qualify a contract
contract = Stock('TSLA', 'SMART', 'USD')
details = ib.reqContractDetails(contract)
print(details[0])
```

---

### 2. Contract Details

**Link**: [contract_details.ipynb](https://nbviewer.jupyter.org/github/erdewit/ib_insync/tree/master/notebooks/contract_details.ipynb)

**Topics Covered**:
- Requesting detailed contract information
- Contract lookup and disambiguation
- Batch contract qualification
- Pattern matching for symbol search
- Working with DataFrames for contract comparison

**Key Operations**:
- `reqContractDetails()` - Get full contract specifications
- `qualifyContracts()` - Enrich basic contracts with IB details
- `reqMatchingSymbols()` - Search for contracts matching text patterns

**Example Usage**:
```python
# Search for AMD contracts
contract = Stock('AMD')
contracts = ib.reqContractDetails(contract)
print(f"Found {len(contracts)} contracts")

# Convert to DataFrame
import pandas as pd
df = pd.DataFrame([c.contract for c in contracts])
print(df[['symbol', 'exchange', 'currency', 'conId']])

# Qualify specific contract
specific = Stock('AMD', 'SMART', 'USD')
qualified = ib.qualifyContracts(specific)
print(f"ConId: {qualified[0].conId}")
print(f"Primary Exchange: {qualified[0].primaryExchange}")

# Pattern matching
matches = ib.reqMatchingSymbols('micro')
for match in matches:
    print(f"{match.contract.symbol}: {match.contract.secType}")
```

**Important Notes**:
- Non-existent symbols return empty results (no errors thrown)
- Multiple matches require more specific contract parameters
- `qualifyContracts()` filters out invalid contracts automatically

---

### 3. Option Chain

**Link**: [option_chain.ipynb](https://nbviewer.jupyter.org/github/erdewit/ib_insync/tree/master/notebooks/option_chain.ipynb)

**Topics Covered**:
- Requesting option chains for underlying securities
- Filtering options by expiration and strike
- Calculating Greeks and implied volatility
- Building option strategies
- Visualizing option data

**Example Usage**:
```python
# Get option chain
stock = Stock('SPY', 'SMART', 'USD')
ib.qualifyContracts(stock)

chains = ib.reqSecDefOptParams(
    stock.symbol,
    '',
    stock.secType,
    stock.conId
)

# Extract expirations and strikes
chain = chains[0]
print(f"Expirations: {chain.expirations}")
print(f"Strikes: {chain.strikes}")

# Create specific option contract
option = Option('SPY', '20240315', 450, 'C', 'SMART')
ib.qualifyContracts(option)

# Get option market data
ticker = ib.reqMktData(option)
ib.sleep(2)

print(f"Bid: {ticker.bid}, Ask: {ticker.ask}")
print(f"Implied Vol: {ticker.impliedVol}")
print(f"Delta: {ticker.modelGreeks.delta}")
```

---

### 4. Bar Data

**Link**: [bar_data.ipynb](https://nbviewer.jupyter.org/github/erdewit/ib_insync/tree/master/notebooks/bar_data.ipynb)

**Topics Covered**:
- Historical bar data requests
- Real-time bar streaming
- Different bar sizes and timeframes
- Data conversion to pandas DataFrames
- Handling different data types (TRADES, MIDPOINT, BID, ASK)

**Example Usage**:
```python
# Historical bars
contract = Stock('AAPL', 'SMART', 'USD')

bars = ib.reqHistoricalData(
    contract,
    endDateTime='',
    durationStr='30 D',
    barSizeSetting='1 hour',
    whatToShow='TRADES',
    useRTH=True
)

# Convert to DataFrame
df = pd.DataFrame(bars)
print(df.head())

# Real-time bars (5-second bars only)
rtBars = ib.reqRealTimeBars(
    contract,
    5,
    'MIDPOINT',
    False
)

# Streaming historical bars
streamingBars = ib.reqHistoricalData(
    contract,
    endDateTime='',
    durationStr='1 D',
    barSizeSetting='1 min',
    whatToShow='TRADES',
    useRTH=True,
    keepUpToDate=True  # Continues updating in real-time
)
```

**Bar Size Options**:
- `'1 secs'`, `'5 secs'`, `'10 secs'`, `'15 secs'`, `'30 secs'`
- `'1 min'`, `'2 mins'`, `'3 mins'`, `'5 mins'`, `'10 mins'`, `'15 mins'`, `'30 mins'`
- `'1 hour'`, `'2 hours'`, `'3 hours'`, `'4 hours'`, `'8 hours'`
- `'1 day'`, `'1 week'`, `'1 month'`

---

### 5. Tick Data

**Link**: [tick_data.ipynb](https://nbviewer.jupyter.org/github/erdewit/ib_insync/tree/master/notebooks/tick_data.ipynb)

**Topics Covered**:
- Real-time tick data streaming
- Tick-by-tick data (most granular level)
- Different tick types and processing
- Event-driven tick handling
- Managing subscription limits

**Example Usage**:
```python
# Market data ticks
contract = Forex('EURUSD')
ticker = ib.reqMktData(contract, '', False, False)

# Event handler for updates
def onTickerUpdate(ticker):
    print(f"Bid: {ticker.bid}, Ask: {ticker.ask}, Last: {ticker.last}")

ticker.updateEvent += onTickerUpdate

# Tick-by-tick data (limit: 3 concurrent subscriptions)
tickByTickData = ib.reqTickByTickData(
    contract,
    'BidAsk',  # Can be: Last, AllLast, BidAsk, MidPoint
    0,         # numberOfTicks (0 = unlimited)
    False      # ignoreSize
)

# Access tick data
for tick in tickByTickData:
    print(tick)
```

**Important Notes**:
- Market data subscription limits: typically 100 concurrent lines
- Tick-by-tick subscription limit: only 3 concurrent subscriptions
- Ticks are cleared after each update - process immediately in event handlers

---

### 6. Market Depth

**Link**: [market_depth.ipynb](https://nbviewer.jupyter.org/github/erdewit/ib_insync/tree/master/notebooks/market_depth.ipynb)

**Topics Covered**:
- Order book (Level II) data
- Market depth streaming
- DOM (Depth of Market) visualization
- Analyzing bid/ask liquidity

**Example Usage**:
```python
# Request market depth
contract = Stock('AAPL', 'SMART', 'USD')
ticker = ib.reqMktDepth(contract)

ib.sleep(2)

# Display order book
print("BIDS:")
for level in ticker.domBids[:10]:
    print(f"  {level.position}: {level.price} x {level.size}")

print("\nASKS:")
for level in ticker.domAsks[:10]:
    print(f"  {level.position}: {level.price} x {level.size}")

# Event handler for depth updates
def onDepthUpdate(ticker):
    print(f"Depth updated: {len(ticker.domBids)} bids, {len(ticker.domAsks)} asks")

ticker.updateEvent += onDepthUpdate
```

**Requirements**:
- Level II market data subscription required
- Not available for all contract types

---

### 7. Ordering

**Link**: [ordering.ipynb](https://nbviewer.jupyter.org/github/erdewit/ib_insync/tree/master/notebooks/ordering.ipynb)

**Topics Covered**:
- Placing various order types
- Order status monitoring
- Modifying and canceling orders
- Trade object lifecycle
- Commission estimation with whatIfOrder()

**⚠️ WARNING**: This notebook places live orders. Use a paper trading account during market hours.

**Example Usage**:
```python
# Create contract
contract = Forex('EURUSD')
ib.qualifyContracts(contract)

# Place limit order
order = LimitOrder('BUY', 20000, 1.1000)
trade = ib.placeOrder(contract, order)

# Monitor order status
print(f"Order status: {trade.orderStatus.status}")
print(f"Order ID: {trade.order.orderId}")

# Wait for completion
while not trade.isDone():
    ib.waitOnUpdate()

print(f"Filled at: {trade.orderStatus.avgFillPrice}")

# Modify order
order.lmtPrice = 1.0950
ib.placeOrder(contract, order)

# Cancel order
ib.cancelOrder(order)

# Estimate commission without placing order
whatif = ib.whatIfOrder(contract, MarketOrder('BUY', 20000))
print(f"Estimated commission: {whatif.commission}")
print(f"Estimated margin: {whatif.initMarginChange}")
```

**Key Concepts**:
- `Trade` object contains order, status, fills, and log
- `trade.isDone()` checks if order is complete
- `whatIfOrder()` provides cost estimates without execution

---

### 8. Scanners

**Link**: [scanners.ipynb](https://nbviewer.jupyter.org/github/erdewit/ib_insync/tree/master/notebooks/scanners.ipynb)

**Topics Covered**:
- Market scanner subscriptions
- Scanner parameters and filters
- Top gainers, losers, volume leaders
- Custom scanner criteria
- Streaming scanner updates

**Example Usage**:
```python
# Create scanner subscription
sub = ScannerSubscription()
sub.instrument = 'STK'
sub.locationCode = 'STK.US.MAJOR'
sub.scanCode = 'TOP_PERC_GAIN'

# One-time scan
scanData = ib.reqScannerData(sub)

for item in scanData:
    print(f"{item.rank}: {item.contract.symbol} - {item.distance}%")

# Streaming scanner
streamingData = ib.reqScannerSubscription(sub)

def onScannerUpdate(data):
    print(f"Scan update at {pd.Timestamp.now()}")
    for item in data[:5]:
        print(f"  {item.contract.symbol}")

streamingData.updateEvent += onScannerUpdate

# Get available scanner parameters
params = ib.reqScannerParameters()
print(params)  # XML document with all options
```

**Common Scanner Codes**:
- `'TOP_PERC_GAIN'` - Biggest percentage gainers
- `'TOP_PERC_LOSE'` - Biggest percentage losers
- `'MOST_ACTIVE'` - Highest volume
- `'HOT_BY_VOLUME'` - Unusually high volume
- `'TOP_TRADE_COUNT'` - Most trades
- `'HOT_BY_PRICE'` - Significant price movement

---

## General Tips for Notebook Usage

### 1. Event Loop Setup
Always start with `util.startLoop()` in Jupyter notebooks to enable nested event loops:

```python
from ib_insync import *
util.startLoop()
```

### 2. Never Use time.sleep()
Use `ib.sleep()` instead to prevent blocking the event loop:

```python
# WRONG
import time
time.sleep(2)

# CORRECT
ib.sleep(2)
```

### 3. Enable Logging
For debugging, enable console logging:

```python
util.logToConsole()  # Shows all log messages
util.logToConsole('INFO')  # Shows INFO and above
util.logToConsole('DEBUG')  # Shows all including debug
```

### 4. Proper Disconnection
Always disconnect cleanly when done:

```python
ib.sleep(1)  # Allow pending data to complete
ib.disconnect()
```

### 5. Paper Trading
When experimenting with orders, always use paper trading:

```python
# Paper trading port is typically 7497
ib.connect('127.0.0.1', 7497, clientId=1)

# Live trading port is typically 7496 (use with caution!)
# ib.connect('127.0.0.1', 7496, clientId=1)
```

---

## Running Notebooks Locally

### Installation

```bash
# Install ib_insync
pip install ib_insync

# Install Jupyter
pip install jupyter

# Install pandas for data analysis
pip install pandas

# Optional: plotting libraries
pip install matplotlib plotly
```

### Download Notebooks

```bash
# Clone the repository
git clone https://github.com/erdewit/ib_insync.git

# Navigate to notebooks directory
cd ib_insync/notebooks

# Start Jupyter
jupyter notebook
```

### Requirements

1. **TWS or IB Gateway** must be running with API enabled
2. **Paper trading account** recommended for testing
3. **Market data subscriptions** for real-time data
4. **Python 3.6+** installed

---

## Additional Resources

- **Official Documentation**: https://ib-insync.readthedocs.io/
- **GitHub Repository**: https://github.com/erdewit/ib_insync
- **User Group**: https://groups.io/g/insync
- **API Reference**: [ib.md](ib.md)
- **Complete Guide**: [ib_insync_complete_guide.md](ib_insync_complete_guide.md)
- **Recipes**: [recipes.md](recipes.md)

---

## Troubleshooting

### "RuntimeError: This event loop is already running"

**Solution**: Use `util.startLoop()` or `util.patchAsyncio()` at the start of your notebook.

```python
from ib_insync import *
util.startLoop()  # Fixes the error
```

### No Data Received

**Possible causes**:
1. TWS/Gateway not running or API not enabled
2. Wrong port number (paper: 7497, live: 7496)
3. Client ID conflict (use unique clientId)
4. Market closed (use `useRTH=False` for extended hours)
5. Missing market data subscriptions

### Connection Refused

**Solution**: Check TWS/Gateway settings:
1. Enable ActiveX and Socket Clients
2. Add 127.0.0.1 to trusted IPs
3. Verify port number matches your connection
4. Check firewall settings

---

## Best Practices

1. ✅ Always use `util.startLoop()` in notebooks
2. ✅ Use `ib.sleep()` instead of `time.sleep()`
3. ✅ Qualify contracts before use
4. ✅ Use event handlers for real-time data
5. ✅ Test with paper trading first
6. ✅ Add delays before disconnecting
7. ✅ Remove event handlers before unsubscribing
8. ✅ Handle errors gracefully
9. ✅ Monitor subscription limits
10. ✅ Keep notebooks clean and well-documented

---

Happy trading with ib_insync! 🚀
