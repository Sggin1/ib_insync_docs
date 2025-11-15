# ib-insync Complete API Reference
**Version: 0.9.86 | Python 3.6+ | For RAG Processing**

> **Library Purpose**: Pythonic sync/async framework for Interactive Brokers TWS API  
> **Key Features**: Auto-sync state management, asyncio-based, Jupyter notebook support  
> **Installation**: `pip install ib-insync`  
> **Requirements**: TWS/IB Gateway (v1023+), API port enabled, "Download open orders" checked

---

## 📋 Table of Contents

1. [Quick Start & Core Concepts](#quick-start)
2. [IB Class - Main Interface](#ib-class)
3. [Connection Management](#connection)
4. [Contract Types](#contracts)
5. [Order Management](#orders)
6. [Market Data](#market-data)
7. [Account & Portfolio](#account)
8. [Historical Data](#historical)
9. [Real-Time Data Streaming](#realtime)
10. [Events System](#events)
11. [Utilities](#utilities)
12. [Best Practices](#best-practices)
13. [Common Patterns](#patterns)
14. [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start {#quick-start}

### Minimal Example
```python
from ib_insync import *

# Jupyter notebook? Uncomment:
# util.startLoop()

ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)

# Get account info
account = ib.managedAccounts()[0]
print(f"Connected to account: {account}")

# Create contract
contract = Stock('AAPL', 'SMART', 'USD')

# Get market data
ticker = ib.reqMktData(contract)
ib.sleep(2)  # Wait for data
print(ticker.marketPrice())

ib.disconnect()
```

### Core Concepts

**Event Loop**: Built on asyncio
- Blocking methods: `connect()`, `reqHistoricalData()`
- Async methods: `connectAsync()`, `reqHistoricalDataAsync()`

**Auto-Sync State**: IB object maintains current state
- Orders: `ib.orders()`
- Positions: `ib.positions()`
- Tickers: `ib.tickers()`

**Never use `time.sleep()`** - Use `ib.sleep()` instead

---

## 🔌 IB Class - Main Interface {#ib-class}

### Class Definition
```python
class IB:
    """High-level interface to Interactive Brokers"""
```

### Class Attributes
```python
RequestTimeout: float = 0        # Request timeout (0 = infinite)
RaiseRequestErrors: bool = False # Raise errors vs silent fail
MaxSyncedSubAccounts: int = 50   # Max sub-accounts to sync
```

### Events
```python
events = (
    'connectedEvent',       # Connection established
    'disconnectedEvent',    # Connection lost
    'updateEvent',          # Any state update
    'pendingTickersEvent',  # Ticker updates available
    'barUpdateEvent',       # Real-time bar update
    'newOrderEvent',        # New order created
    'orderModifyEvent',     # Order modified
    'cancelOrderEvent',     # Order cancel requested
    'openOrderEvent',       # Open order status
    'orderStatusEvent',     # Order status changed
    'execDetailsEvent',     # Trade execution details
    'commissionReportEvent',# Commission report
    'updatePortfolioEvent', # Portfolio updated
    'positionEvent',        # Position changed
    'accountValueEvent',    # Account value updated
    'accountSummaryEvent',  # Account summary updated
    'pnlEvent',            # PnL update
    'pnlSingleEvent',      # Single position PnL
    'scannerDataEvent',    # Scanner data received
    'tickNewsEvent',       # News tick
    'newsBulletinEvent',   # News bulletin
    'errorEvent',          # Error occurred
    'timeoutEvent'         # Request timeout
)
```

### State Properties
```python
# Access current state (auto-synced)
ib.accountValues()      # List[AccountValue]
ib.portfolio()          # List[PortfolioItem]
ib.positions()          # List[Position]
ib.trades()             # List[Trade]
ib.openTrades()         # List[Trade] - open only
ib.orders()             # List[Order]
ib.openOrders()         # List[Order] - open only
ib.fills()              # List[Fill]
ib.executions()         # List[Execution]
ib.tickers()            # List[Ticker]
ib.pendingTickers()     # Set[Ticker] - with updates
ib.reqId()              # int - next request ID
```

---

## 🔗 Connection Management {#connection}

### Connect (Blocking)
```python
ib.connect(
    host: str = '127.0.0.1',
    port: int = 7497,           # 7497=TWS, 4001=Gateway
    clientId: int = 1,          # Unique per connection
    timeout: float = 2.0,       # Connection timeout (0=no limit)
    readonly: bool = False,     # Read-only mode
    account: str = '',          # Main account for updates
    raiseSyncErrors: bool = True # Raise sync errors
) -> None
```

**Returns**: None (blocks until connected)

**clientId Notes**:
- clientId=0: Auto-merge manual TWS orders
- Must be unique per connection
- Different clientIds see different order states

### Connect (Async)
```python
await ib.connectAsync(
    host, port, clientId, 
    timeout, readonly, account, raiseSyncErrors
) -> None
```

### Disconnect
```python
ib.disconnect() -> None
```
Clears all session state.

### Check Connection
```python
ib.isConnected() -> bool
ib.client.isReady() -> bool  # API ready
```

### Wait & Sleep
```python
ib.waitOnUpdate(timeout: float = 0) -> bool
# Wait for network update. Returns False on timeout.

ib.sleep(seconds: float = 0.02) -> None
# Sleep while keeping event loop alive
# ALWAYS use this instead of time.sleep()
```

### Loop Management
```python
ib.run()  # Run until disconnect
await ib.runAsync()  # Async version

# Condition-based iteration
for update in ib.loopUntil(timeout=60):
    if condition:
        break
```

---

## 📄 Contract Types {#contracts}

### Base Contract
```python
@dataclass
class Contract:
    conId: int = 0              # Unique IB contract ID
    symbol: str = ''            # Ticker symbol
    secType: str = ''           # Security type
    lastTradeDateOrContractMonth: str = ''
    strike: float = 0.0
    right: str = ''             # 'C' or 'P' for options
    multiplier: str = ''
    exchange: str = ''
    primaryExchange: str = ''
    currency: str = ''
    localSymbol: str = ''
    tradingClass: str = ''
    includeExpired: bool = False
    secIdType: str = ''         # CUSIP, SEDOL, ISIN, RIC
    secId: str = ''
    description: str = ''
    issuerId: str = ''
    comboLegsDescrip: str = ''
    comboLegs: List = None      # For combo orders
    deltaNeutralContract: DeltaNeutralContract = None
```

### Stock
```python
Stock(
    symbol: str,
    exchange: str = 'SMART',
    currency: str = 'USD',
    primaryExchange: str = ''
)

# Examples
Stock('AAPL', 'SMART', 'USD')
Stock('INTC', 'SMART', 'USD', primaryExchange='NASDAQ')
Stock('BMW', 'SMART', 'EUR', primaryExchange='IBIS')
```

### Forex
```python
Forex(pair: str = 'EURUSD', exchange: str = 'IDEALPRO')

# Examples
Forex('EURUSD')
Forex('GBPUSD')
```

### Future
```python
Future(
    symbol: str = '',
    lastTradeDateOrContractMonth: str = '',
    exchange: str = '',
    multiplier: str = '',
    currency: str = ''
)

# Examples
Future('ES', '20240920', 'GLOBEX')  # E-mini S&P
Future('CL', '202412', 'NYMEX')     # Crude Oil
```

### Option
```python
Option(
    symbol: str = '',
    lastTradeDateOrContractMonth: str = '',
    strike: float = 0.0,
    right: str = '',            # 'C' or 'P'
    exchange: str = '',
    multiplier: str = '',
    currency: str = ''
)

# Examples
Option('SPY', '20240920', 450, 'C', 'SMART')  # Call
Option('AAPL', '20240315', 180, 'P', 'SMART') # Put
```

### Index
```python
Index(symbol: str = '', exchange: str = '')

# Examples
Index('SPX', 'CBOE')
Index('VIX', 'CBOE')
```

### CFD
```python
CFD(symbol: str = '', exchange: str = '', currency: str = '')

# Example
CFD('IBUS30')
```

### Commodity
```python
Commodity(
    symbol: str = '',
    exchange: str = '',
    currency: str = ''
)

# Example
Commodity('XAUUSD', 'SMART', 'USD')
```

### Bond
```python
Bond(secIdType: str = '', secId: str = '')

# Example
Bond(secIdType='ISIN', secId='US03076KAA60')
```

### Crypto
```python
Crypto(symbol: str = '', exchange: str = '', currency: str = '')

# Example
Crypto('BTC', 'PAXOS', 'USD')
```

### Contract by conId
```python
Contract(conId=270639)  # Direct lookup by IB contract ID
```

### Qualify Contracts
```python
# Resolve ambiguous contracts
contracts = ib.qualifyContracts(contract)
# Returns list of fully qualified contracts

# Example
stock = Stock('AAPL', 'SMART', 'USD')
qualified = ib.qualifyContracts(stock)[0]
print(qualified.conId)  # IB contract ID
```

### Contract Details
```python
details = ib.reqContractDetails(contract)
# Returns List[ContractDetails]

# ContractDetails fields:
# .contract - Fully qualified contract
# .marketName
# .minTick
# .priceMagnifier
# .orderTypes
# .validExchanges
# .underConId
# .longName
# .contractMonth
# .industry
# .category
# .subcategory
# .timeZoneId
# .tradingHours
# .liquidHours
# And many more...
```

### Match Symbols
```python
descriptions = ib.reqMatchingSymbols('app')
# Returns List[ContractDescription]
# Fuzzy search for symbols
```

---

## 📦 Order Management {#orders}

### Order Types

#### Base Order
```python
@dataclass
class Order:
    orderId: int = 0
    clientId: int = 0
    permId: int = 0
    action: str = ''            # 'BUY' or 'SELL'
    totalQuantity: float = 0.0
    orderType: str = ''         # See order types below
    lmtPrice: float = 0.0
    auxPrice: float = 0.0       # Stop price
    tif: str = 'DAY'            # Time in force
    
    # Advanced fields
    ocaGroup: str = ''          # One-Cancels-All group
    account: str = ''
    openClose: str = 'O'        # 'O'=open, 'C'=close
    origin: int = 0             # 0=customer
    orderRef: str = ''
    transmit: bool = True       # Auto-transmit
    parentId: int = 0           # For bracket orders
    blockOrder: bool = False
    sweepToFill: bool = False
    displaySize: int = 0
    triggerMethod: int = 0
    outsideRth: bool = False    # Outside regular hours
    hidden: bool = False
    
    # Order combos
    goodAfterTime: str = ''
    goodTillDate: str = ''
    rule80A: str = ''
    allOrNone: bool = False
    minQty: int = None
    percentOffset: float = None
    overridePercentageConstraints: bool = False
    trailStopPrice: float = None
    trailingPercent: float = None
    
    # Financial advisors
    faGroup: str = ''
    faProfile: str = ''
    faMethod: str = ''
    faPercentage: str = ''
    
    # Institutional
    designatedLocation: str = ''
    exemptCode: int = -1
    
    # Smart routing
    discretionaryAmt: float = 0.0
    eTradeOnly: bool = False
    firmQuoteOnly: bool = False
    nbboPriceCap: float = None
    optOutSmartRouting: bool = False
    
    # Pegged orders
    stockRefPrice: float = None
    delta: float = None
    
    # Volatility orders
    volatility: float = None
    volatilityType: int = None
    deltaNeutralOrderType: str = ''
    deltaNeutralAuxPrice: float = None
    deltaNeutralConId: int = 0
    deltaNeutralShortSale: bool = False
    deltaNeutralShortSaleSlot: int = 0
    deltaNeutralDesignatedLocation: str = ''
    continuousUpdate: bool = False
    referencePriceType: int = None
    
    # Conditions
    conditions: List = None
    conditionsIgnoreRth: bool = False
    conditionsCancelOrder: bool = False
    
    # Algo orders
    algoStrategy: str = ''
    algoParams: List = None
    
    # What-if
    whatIf: bool = False
    
    # Misc
    notHeld: bool = False
    solicited: bool = False
    randomizeSize: bool = False
    randomizePrice: bool = False
    
    # Pegged to benchmark
    referenceContractId: int = 0
    peggedChangeAmount: float = 0.0
    isPeggedChangeAmountDecrease: bool = False
    referenceChangeAmount: float = 0.0
    referenceExchangeId: str = ''
    adjustedOrderType: str = ''
    
    # Misc2
    modelCode: str = ''
    extOperator: str = ''
    cashQty: float = None
    mifid2DecisionMaker: str = ''
    mifid2DecisionAlgo: str = ''
    mifid2ExecutionTrader: str = ''
    mifid2ExecutionAlgo: str = ''
    dontUseAutoPriceForHedge: bool = False
    
    # Manual times (for audit)
    manualOrderTime: str = ''
    manualOrderCancelTime: str = ''
    
    # Post to ATS
    usePriceMgmtAlgo: bool = None
```

#### Market Order
```python
MarketOrder(action: str, totalQuantity: float, **kwargs)

# Examples
order = MarketOrder('BUY', 100)
order = MarketOrder('SELL', 50, tif='GTC')
```

#### Limit Order
```python
LimitOrder(
    action: str,
    totalQuantity: float,
    lmtPrice: float,
    **kwargs
)

# Examples
order = LimitOrder('BUY', 100, 150.50)
order = LimitOrder('SELL', 50, 155.00, tif='GTC')
```

#### Stop Order
```python
StopOrder(
    action: str,
    totalQuantity: float,
    stopPrice: float,
    **kwargs
)

# Examples
order = StopOrder('SELL', 100, 145.00)  # Stop loss
```

#### Stop-Limit Order
```python
StopLimitOrder(
    action: str,
    totalQuantity: float,
    lmtPrice: float,
    stopPrice: float,
    **kwargs
)

# Example
order = StopLimitOrder('SELL', 100, 148.00, 150.00)
```

#### Bracket Order
```python
BracketOrder(
    action: str,
    quantity: float,
    limitPrice: float,
    takeProfitPrice: float,
    stopLossPrice: float
) -> Tuple[Order, Order, Order]

# Returns (parent, takeProfit, stopLoss)
# Example
parent, takeProfit, stopLoss = BracketOrder(
    'BUY', 100, 150.0, 160.0, 145.0
)
```

### Place Order
```python
trade = ib.placeOrder(contract: Contract, order: Order) -> Trade
# Returns Trade object (live-updated)

# Example
contract = Stock('AAPL', 'SMART', 'USD')
order = LimitOrder('BUY', 100, 150.0)
trade = ib.placeOrder(contract, order)

# Trade object updated in real-time:
# - trade.orderStatus
# - trade.fills
# - trade.log
```

### Modify Order
```python
# Modify existing order
order.lmtPrice = 151.0
trade = ib.placeOrder(contract, order)
```

### Cancel Order
```python
trade = ib.cancelOrder(order: Order) -> Trade

# Cancel all orders
ib.reqGlobalCancel()
```

### Order Status
```python
@dataclass
class OrderStatus:
    orderId: int = 0
    status: str = ''        # PendingSubmit, Submitted, Filled, Cancelled, etc.
    filled: float = 0.0
    remaining: float = 0.0
    avgFillPrice: float = 0.0
    permId: int = 0
    parentId: int = 0
    lastFillPrice: float = 0.0
    clientId: int = 0
    whyHeld: str = ''
    mktCapPrice: float = 0.0
```

**Status Values**:
- PendingSubmit
- PendingCancel
- PreSubmitted
- Submitted
- ApiCancelled
- Cancelled
- Filled
- Inactive

### Trade Object
```python
@dataclass
class Trade:
    contract: Contract = None
    order: Order = None
    orderStatus: OrderStatus = None
    fills: List[Fill] = []
    log: List[TradeLogEntry] = []
    
    # Methods
    def isActive(self) -> bool
    def isDone(self) -> bool
    def filled(self) -> float
    def remaining(self) -> float
```

### What-If Order
```python
orderState = ib.whatIfOrder(contract, order)
# Test order without placing
# Returns OrderState with commission/margin impact

# OrderState fields:
# .initMarginBefore
# .maintMarginBefore
# .equityWithLoanBefore
# .initMarginAfter
# .maintMarginAfter
# .equityWithLoanAfter
# .commission
# .minCommission
# .maxCommission
# .commissionCurrency
```

### Order Types Reference

**Market Orders**:
- `MKT` - Market order
- `MIDPRICE` - Midpoint order

**Limit Orders**:
- `LMT` - Limit order
- `MIT` - Market-if-touched
- `LIT` - Limit-if-touched

**Stop Orders**:
- `STP` - Stop order
- `STP LMT` - Stop limit
- `TRAIL` - Trailing stop
- `TRAIL LIMIT` - Trailing stop limit

**Pegged Orders**:
- `PEG MID` - Pegged to midpoint
- `PEG BEST` - Pegged to best bid/ask
- `PEG STK` - Pegged to stock

**Time-in-Force Options**:
- `DAY` - Day order (default)
- `GTC` - Good-till-cancelled
- `IOC` - Immediate-or-cancel
- `GTD` - Good-till-date
- `OPG` - Market on open
- `FOK` - Fill-or-kill

---

## 📊 Market Data {#market-data}

### Request Market Data (Streaming)
```python
ticker = ib.reqMktData(
    contract: Contract,
    genericTickList: str = '',
    snapshot: bool = False,
    regulatorySnapshot: bool = False,
    mktDataOptions: List = None
) -> Ticker

# Ticker auto-updates in real-time
```

**Generic Tick List IDs**:
```
100 - putVolume, callVolume (options)
101 - putOpenInterest, callOpenInterest (options)
104 - histVolatility (options)
105 - avOptionVolume (options)
106 - impliedVolatility (options)
162 - indexFuturePremium
165 - low13week, high13week, low26week, high26week,
      low52week, high52week, avVolume
221 - markPrice
225 - auctionVolume, auctionPrice, auctionImbalance
233 - last, lastSize, rtVolume, rtTime, vwap (Time & Sales)
236 - shortableShares
258 - fundamentalRatios
```

**Example**:
```python
contract = Stock('AAPL', 'SMART', 'USD')
ticker = ib.reqMktData(contract, genericTickList='233,236')
ib.sleep(2)
print(f"Last: {ticker.last}")
print(f"Bid: {ticker.bid}")
print(f"Ask: {ticker.ask}")
print(f"Volume: {ticker.volume}")
```

### Cancel Market Data
```python
ib.cancelMktData(contract: Contract) -> None
```

### Ticker Object
```python
@dataclass
class Ticker:
    contract: Contract = None
    time: datetime = None
    
    # Bid/Ask
    bid: float = nan
    bidSize: float = nan
    bidExchange: str = ''
    ask: float = nan
    askSize: float = nan
    askExchange: str = ''
    
    # Last trade
    last: float = nan
    lastSize: float = nan
    lastExchange: str = ''
    
    # Volume
    volume: float = nan
    volumeRate: float = nan
    
    # Prices
    open: float = nan
    high: float = nan
    low: float = nan
    close: float = nan
    vwap: float = nan
    
    # Options
    putVolume: float = nan
    callVolume: float = nan
    putOpenInterest: float = nan
    callOpenInterest: float = nan
    avOptionVolume: float = nan
    impliedVolatility: float = nan
    histVolatility: float = nan
    
    # Greeks (options)
    delta: float = nan
    gamma: float = nan
    theta: float = nan
    vega: float = nan
    
    # Market depth
    domBids: List = []
    domAsks: List = []
    domTicks: List = []
    
    # Ticks
    ticks: List = []
    tickByTicks: List = []
    
    # Halted
    halted: float = nan
    
    # Real-time
    rtVolume: float = nan
    rtTime: datetime = None
    rtHistVolativity: float = nan
    rtTradeVolume: float = nan
    
    # Methods
    def marketPrice(self) -> float
    def hasBidAsk(self) -> bool
    def midpoint(self) -> float
```

### Market Depth (Level II)
```python
ticker = ib.reqMktDepth(
    contract: Contract,
    numRows: int = 5,
    isSmartDepth: bool = False,
    mktDepthOptions: List = None
) -> Ticker

# Ticker.domBids and Ticker.domAsks auto-update
```

### Cancel Market Depth
```python
ib.cancelMktDepth(contract: Contract) -> None
```

### Tick-by-Tick Data
```python
ticker = ib.reqTickByTickData(
    contract: Contract,
    tickType: str,  # 'Last', 'BidAsk', 'AllLast', 'MidPoint'
    numberOfTicks: int = 0,
    ignoreSize: bool = False
) -> Ticker

# Ticker.tickByTicks auto-updates
```

### Market Data Type
```python
ib.reqMarketDataType(marketDataType: int) -> None
# 1 = Live
# 2 = Frozen
# 3 = Delayed
# 4 = Delayed-Frozen
```

---

## 📈 Historical Data {#historical}

### Request Historical Data
```python
bars = ib.reqHistoricalData(
    contract: Contract,
    endDateTime: str = '',      # '' = now, or 'YYYYMMDD HH:MM:SS'
    durationStr: str = '1 D',   # '60 S', '30 D', '13 W', '6 M', '1 Y'
    barSizeSetting: str = '1 hour',
    whatToShow: str = 'TRADES', # See below
    useRTH: bool = True,        # Regular trading hours only
    formatDate: int = 1,        # 1=yyyyMMdd HH:mm:ss, 2=epoch
    keepUpToDate: bool = False, # Auto-update
    chartOptions: List = None,
    timeout: float = 60
) -> BarDataList

# Returns BarDataList (auto-synced if keepUpToDate=True)
```

**Duration Strings**:
```
S = Seconds (max 60)
D = Days (max 365)
W = Weeks (max 52)
M = Months (max 12)
Y = Years (max 1)
```

**Bar Sizes**:
```
'1 secs', '5 secs', '10 secs', '15 secs', '30 secs',
'1 min', '2 mins', '3 mins', '5 mins', '10 mins', '15 mins', '20 mins', '30 mins',
'1 hour', '2 hours', '3 hours', '4 hours', '8 hours',
'1 day', '1 week', '1 month'
```

**What to Show**:
```
'TRADES'           - Actual trades
'MIDPOINT'         - Bid/ask midpoint
'BID'              - Bid prices
'ASK'              - Ask prices
'BID_ASK'          - Bid/ask pairs
'HISTORICAL_VOLATILITY'
'OPTION_IMPLIED_VOLATILITY'
'REBATE_RATE'
'FEE_RATE'
'YIELD_BID'
'YIELD_ASK'
'YIELD_BID_ASK'
'YIELD_LAST'
```

**Example**:
```python
contract = Forex('EURUSD')
bars = ib.reqHistoricalData(
    contract,
    endDateTime='',
    durationStr='30 D',
    barSizeSetting='1 hour',
    whatToShow='MIDPOINT',
    useRTH=True
)

# Convert to pandas
import pandas as pd
df = util.df(bars)
print(df.head())
```

### Bar Object
```python
@dataclass
class Bar:
    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    average: float
    barCount: int
```

### Historical Ticks
```python
ticks = ib.reqHistoricalTicks(
    contract: Contract,
    startDateTime: str,
    endDateTime: str,
    numberOfTicks: int = 1000,
    whatToShow: str = 'TRADES',  # 'TRADES', 'BID_ASK', 'MIDPOINT'
    useRth: bool = True,
    ignoreSize: bool = False,
    miscOptions: List = None
) -> List

# Returns list of HistoricalTick objects
```

### Head Timestamp
```python
headTimestamp = ib.reqHeadTimeStamp(
    contract: Contract,
    whatToShow: str = 'TRADES',
    useRTH: bool = True,
    formatDate: int = 1
) -> str

# Earliest available data timestamp
```

### Historical Schedule
```python
schedule = ib.reqHistoricalSchedule(
    contract: Contract,
    numDays: int = 1,
    endDateTime: str = '',
    useRTH: bool = True
) -> List[HistoricalSchedule]

# Trading schedule for contract
```

---

## ⏱️ Real-Time Data {#realtime}

### Real-Time Bars
```python
bars = ib.reqRealTimeBars(
    contract: Contract,
    barSize: int = 5,           # Only 5 supported
    whatToShow: str = 'TRADES', # TRADES, MIDPOINT, BID, ASK
    useRTH: bool = False,
    realTimeBarsOptions: List = None
) -> RealTimeBarList

# Returns RealTimeBarList (auto-updating)
# bars.updateEvent fires on new bar
```

**⚠️ BEST PRACTICE**: 
- **Don't use reqHistoricalData for real-time** - Use reqRealTimeBars or streaming tickers
- reqHistoricalData is for historical backtesting only
- Real-time feeds are more efficient and don't count against API limits

### Cancel Real-Time Bars
```python
ib.cancelRealTimeBars(bars: RealTimeBarList) -> None
```

### Keep Historical Updated
```python
bars = ib.reqHistoricalData(
    contract,
    endDateTime='',
    durationStr='1 D',
    barSizeSetting='1 min',
    whatToShow='TRADES',
    useRTH=True,
    keepUpToDate=True  # ← Keep updating
)

# bars.updateEvent fires on changes
```

---

## 💰 Account & Portfolio {#account}

### Managed Accounts
```python
accounts = ib.managedAccounts() -> List[str]
# List of account codes
```

### Account Values
```python
values = ib.accountValues(account: str = '') -> List[AccountValue]

# AccountValue fields:
# .account
# .tag      - Key name (e.g., 'NetLiquidation')
# .value    - Value as string
# .currency
# .modelCode
```

**Common Tags**:
```
NetLiquidation      - Total account value
TotalCashValue      - Cash balance
SettledCash         - Settled cash
AccruedCash         - Accrued cash
BuyingPower         - Buying power
EquityWithLoanValue - Stock value + cash
GrossPositionValue  - Total position value
RegTEquity          - RegT equity
RegTMargin          - RegT margin
SMA                 - Special Memo Account
InitMarginReq       - Initial margin
MaintMarginReq      - Maintenance margin
AvailableFunds      - Available funds
ExcessLiquidity     - Excess liquidity
```

### Account Summary
```python
summary = ib.reqAccountSummary() -> List[AccountValue]
# Summary for all accounts

# Or filter by tags
summary = ib.reqAccountSummary(
    account: str = 'All',
    modelCode: str = '',
    tags: str = 'NetLiquidation,TotalCashValue,BuyingPower'
)
```

### Portfolio
```python
portfolio = ib.portfolio(account: str = '') -> List[PortfolioItem]

# PortfolioItem fields:
# .contract
# .position        - Quantity
# .marketPrice     - Current price
# .marketValue     - Position value
# .averageCost     - Avg cost basis
# .unrealizedPNL   - Unrealized P&L
# .realizedPNL     - Realized P&L
# .account
```

### Positions
```python
positions = ib.positions(account: str = '') -> List[Position]

# Position fields:
# .account
# .contract
# .position       - Quantity
# .avgCost        - Average cost
```

### PnL (Profit & Loss)
```python
pnl = ib.reqPnL(account: str, modelCode: str = '') -> PnL
# Start PnL subscription

# PnL fields (live-updated):
# .account
# .modelCode
# .dailyPnL
# .unrealizedPnL
# .realizedPnL

# Cancel
ib.cancelPnL(account: str, modelCode: str = '')
```

### PnL Single Position
```python
pnlSingle = ib.reqPnLSingle(
    account: str,
    modelCode: str,
    conId: int
) -> PnLSingle

# PnLSingle fields (live-updated):
# .account
# .modelCode
# .conId
# .dailyPnL
# .unrealizedPnL
# .realizedPnL
# .position
# .value

# Cancel
ib.cancelPnLSingle(account, modelCode, conId)
```

---

## 🎯 Events System {#events}

### Event Handling
```python
# Events use eventkit library

# Subscribe to event
def onPendingTickers(tickers):
    for ticker in tickers:
        print(f"{ticker.contract.symbol}: {ticker.marketPrice()}")

ib.pendingTickersEvent += onPendingTickers

# Unsubscribe
ib.pendingTickersEvent -= onPendingTickers

# One-time handler
ib.connectedEvent += lambda: print('Connected!')
```

### Trade Events
```python
# New order placed
ib.newOrderEvent += lambda trade: print(f'New order: {trade}')

# Order modified
ib.orderModifyEvent += lambda trade: print(f'Modified: {trade}')

# Order status changed
ib.orderStatusEvent += lambda trade: print(f'Status: {trade.orderStatus.status}')

# Execution received
ib.execDetailsEvent += lambda trade, fill: print(f'Fill: {fill}')

# Commission report
ib.commissionReportEvent += lambda trade, fill, report: print(f'Commission: {report}')
```

### Market Data Events
```python
# Ticker updates
ib.pendingTickersEvent += lambda tickers: handle_tickers(tickers)

# Bar updates
ib.barUpdateEvent += lambda bars, hasNewBar: handle_bars(bars, hasNewBar)

# Scanner data
ib.scannerDataEvent += lambda scanData: print(scanData)
```

### Account Events
```python
# Portfolio updates
ib.updatePortfolioEvent += lambda item: print(f'Portfolio: {item}')

# Position changes
ib.positionEvent += lambda position: print(f'Position: {position}')

# Account value updates
ib.accountValueEvent += lambda value: print(f'{value.tag}: {value.value}')

# PnL updates
ib.pnlEvent += lambda pnl: print(f'PnL: {pnl.dailyPnL}')
```

### Connection Events
```python
# Connected
ib.connectedEvent += lambda: print('Connected to TWS')

# Disconnected
ib.disconnectedEvent += lambda: print('Disconnected')

# Error
ib.errorEvent += lambda reqId, errorCode, errorString, contract: \
    print(f'Error {errorCode}: {errorString}')
```

### Error Codes Reference

**Warnings** (informational):
```
2104 - Market data farm connection OK
2106 - Historical data farm connection OK
2158 - Sec-def data farm connection OK
```

**Errors**:
```
200 - No security definition found
201 - Order rejected
202 - Order cancelled
321 - Error validating request
326 - Unable to connect (check port)
354 - Requested market data not subscribed
404 - Order held
502 - Couldn't connect to TWS
```

---

## 🛠️ Utilities {#utilities}

### Datetime Utilities
```python
# Format for IB
formatted = util.formatIBDatetime(dt: datetime) -> str
# Returns: 'YYYYMMDD HH:MM:SS UTC'

# Parse from IB
parsed = util.parseIBDatetime(s: str) -> Union[date, datetime]
```

### Dataframe Conversion
```python
import pandas as pd

# Bars to DataFrame
df = util.df(bars)

# List of objects to DataFrame
df = util.df(ib.positions())
df = util.df(ib.accountValues())
```

### Logging
```python
# Log to console
util.logToConsole(level=logging.INFO)

# Log to file
util.logToFile('ib_log.txt', level=logging.DEBUG)
```

### Event Loop Integration

#### Jupyter Notebooks
```python
# At start of notebook
util.startLoop()

# Or with old notebooks
util.patchAsyncio()
```

#### Qt Integration
```python
util.useQt('PyQt5')  # or 'PyQt6', 'PySide2', 'PySide6'
# Integrates asyncio with Qt event loop
```

### Schedule Periodic Tasks
```python
def callback():
    print('Periodic task')

# Schedule every 60 seconds
handle = util.schedule(60, callback)

# Cancel scheduled task
handle.cancel()
```

### Time Range Iterator
```python
# Iterate over time periods
for dt in util.timeRange(
    start='20240101',
    end='20240131',
    step='1 day'
):
    print(dt)
```

---

## ✅ Best Practices {#best-practices}

### 1. Use Real-Time Feeds, Not Repeated Historical Requests

**❌ BAD** - Don't poll historical data:
```python
while True:
    bars = ib.reqHistoricalData(...)
    time.sleep(5)  # Also wrong - blocks event loop!
```

**✅ GOOD** - Use streaming:
```python
# For tick data
ticker = ib.reqMktData(contract, '233')  # Last, volume, vwap
ticker.updateEvent += lambda ticker: process_tick(ticker)

# For bar data
bars = ib.reqRealTimeBars(contract, 5, 'TRADES', False)
bars.updateEvent += lambda bars, hasNewBar: process_bar(bars, hasNewBar)
```

### 2. Never Use time.sleep()

**❌ BAD**:
```python
time.sleep(5)  # Blocks event loop!
```

**✅ GOOD**:
```python
ib.sleep(5)  # Keeps event loop running
```

### 3. Qualify Contracts

**❌ BAD** - Ambiguous:
```python
contract = Stock('AAPL', 'SMART', 'USD')
ticker = ib.reqMktData(contract)
```

**✅ GOOD** - Qualified:
```python
contract = Stock('AAPL', 'SMART', 'USD')
contract = ib.qualifyContracts(contract)[0]
ticker = ib.reqMktData(contract)
```

### 4. Handle Events, Don't Poll

**❌ BAD** - Polling:
```python
while True:
    if ticker.last > 150:
        break
    ib.sleep(0.1)
```

**✅ GOOD** - Event-driven:
```python
def on_price_update(ticker):
    if ticker.last > 150:
        take_action()

ticker.updateEvent += on_price_update
```

### 5. Error Handling

**✅ GOOD**:
```python
def on_error(reqId, errorCode, errorString, contract):
    if errorCode == 200:
        print(f"Contract not found: {contract}")
    elif errorCode == 321:
        print(f"Validation error: {errorString}")
    # Handle other errors...

ib.errorEvent += on_error
```

### 6. Cleanup Resources

**✅ GOOD**:
```python
try:
    ticker = ib.reqMktData(contract)
    # ... do work ...
finally:
    ib.cancelMktData(contract)
    ib.disconnect()
```

### 7. Request Throttling

IB limits: **45 requests/second**

**✅ GOOD** - Built-in throttling:
```python
# ib-insync handles throttling automatically
for contract in large_list:
    ib.reqMktData(contract)
# No manual delays needed
```

### 8. Use Bracket Orders for Protection

**✅ GOOD**:
```python
parent, takeProfit, stopLoss = BracketOrder(
    'BUY', 100, 150.0,
    takeProfitPrice=160.0,
    stopLossPrice=145.0
)
for order in (parent, takeProfit, stopLoss):
    ib.placeOrder(contract, order)
```

### 9. Monitor Connection

**✅ GOOD**:
```python
def on_disconnect():
    print("Disconnected! Attempting reconnect...")
    reconnect_logic()

ib.disconnectedEvent += on_disconnect
```

### 10. Set Timeouts

**✅ GOOD**:
```python
ib = IB()
ib.RequestTimeout = 30  # 30 second timeout
ib.RaiseRequestErrors = True  # Raise exceptions

try:
    ib.connect('127.0.0.1', 7497, clientId=1, timeout=10)
except asyncio.TimeoutError:
    print("Connection timeout!")
```

---

## 🔄 Common Patterns {#patterns}

### Pattern: Live Ticker Monitor
```python
from ib_insync import *

ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)

contracts = [
    Stock('AAPL', 'SMART', 'USD'),
    Stock('GOOGL', 'SMART', 'USD'),
    Stock('MSFT', 'SMART', 'USD')
]

contracts = ib.qualifyContracts(*contracts)

def on_pending_tickers(tickers):
    for ticker in tickers:
        symbol = ticker.contract.symbol
        price = ticker.marketPrice()
        volume = ticker.volume
        print(f"{symbol}: ${price:.2f} | Vol: {volume}")

ib.pendingTickersEvent += on_pending_tickers

# Subscribe to all
for contract in contracts:
    ib.reqMktData(contract, '', False, False)

# Run forever
ib.run()
```

### Pattern: Real-Time Bar Processing
```python
from ib_insync import *

ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)

contract = Forex('EURUSD')
contract = ib.qualifyContracts(contract)[0]

def on_bar_update(bars, hasNewBar):
    if hasNewBar:
        bar = bars[-1]
        print(f"New 5s bar: {bar.date} O:{bar.open} H:{bar.high} L:{bar.low} C:{bar.close}")

bars = ib.reqRealTimeBars(contract, 5, 'MIDPOINT', False)
bars.updateEvent += on_bar_update

ib.run()
```

### Pattern: Automated Trading Strategy
```python
from ib_insync import *

ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)

contract = Stock('SPY', 'SMART', 'USD')
contract = ib.qualifyContracts(contract)[0]

# Strategy parameters
quantity = 100
entry_price = None
position = 0

def on_tick(ticker):
    global entry_price, position
    price = ticker.last
    
    if price is None or price != price:  # NaN check
        return
    
    # Entry logic
    if position == 0 and should_enter(price):
        order = MarketOrder('BUY', quantity)
        trade = ib.placeOrder(contract, order)
        entry_price = price
        position = quantity
        print(f"ENTRY: Buy {quantity} @ {price}")
    
    # Exit logic
    elif position > 0 and should_exit(price, entry_price):
        order = MarketOrder('SELL', quantity)
        trade = ib.placeOrder(contract, order)
        profit = (price - entry_price) * quantity
        print(f"EXIT: Sell {quantity} @ {price} | Profit: ${profit:.2f}")
        position = 0
        entry_price = None

def should_enter(price):
    # Your entry logic
    return False

def should_exit(price, entry):
    # Your exit logic (e.g., stop loss, take profit)
    return False

ticker = ib.reqMktData(contract, '233', False, False)
ticker.updateEvent += on_tick

ib.run()
```

### Pattern: Historical Data Download
```python
from ib_insync import *
import pandas as pd

ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)

contract = Stock('AAPL', 'SMART', 'USD')
contract = ib.qualifyContracts(contract)[0]

# Download multiple timeframes
timeframes = [
    ('1 Y', '1 day'),
    ('6 M', '1 hour'),
    ('30 D', '15 mins')
]

all_data = {}
for duration, barsize in timeframes:
    bars = ib.reqHistoricalData(
        contract,
        endDateTime='',
        durationStr=duration,
        barSizeSetting=barsize,
        whatToShow='TRADES',
        useRTH=True
    )
    df = util.df(bars)
    all_data[f'{duration}_{barsize}'] = df
    print(f"Downloaded {len(bars)} {barsize} bars for {duration}")

# Save to files
for name, df in all_data.items():
    df.to_csv(f"{contract.symbol}_{name}.csv", index=False)

ib.disconnect()
```

### Pattern: Portfolio Monitor
```python
from ib_insync import *

ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)

def show_portfolio():
    print("\n=== PORTFOLIO ===")
    for item in ib.portfolio():
        symbol = item.contract.symbol
        pos = item.position
        price = item.marketPrice
        value = item.marketValue
        pnl = item.unrealizedPNL
        print(f"{symbol:6} | Pos: {pos:6} | Price: ${price:8.2f} | Value: ${value:10.2f} | PnL: ${pnl:8.2f}")
    
    print("\n=== ACCOUNT ===")
    values = ib.accountValues()
    important_tags = ['NetLiquidation', 'TotalCashValue', 'BuyingPower', 'GrossPositionValue']
    for value in values:
        if value.tag in important_tags:
            print(f"{value.tag:20} | {value.value:15} {value.currency}")

def on_update(item):
    show_portfolio()

# Show initial state
show_portfolio()

# Update on changes
ib.updatePortfolioEvent += on_update

ib.run()
```

### Pattern: Option Chain Analysis
```python
from ib_insync import *

ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)

underlying = Stock('SPY', 'SMART', 'USD')
underlying = ib.qualifyContracts(underlying)[0]

# Get option chain
chains = ib.reqSecDefOptParams(
    underlying.symbol,
    '',
    underlying.secType,
    underlying.conId
)

print(f"Found {len(chains)} option chains")

# Get chain for specific exchange
chain = next(c for c in chains if c.exchange == 'SMART')
print(f"Trading class: {chain.tradingClass}")
print(f"Expirations: {sorted(chain.expirations)[:5]}")  # First 5
print(f"Strike range: {min(chain.strikes)} - {max(chain.strikes)}")

# Request contracts for specific expiration
expiration = sorted(chain.expirations)[0]
strikes = sorted([s for s in chain.strikes if 400 < s < 500])

contracts = [
    Option('SPY', expiration, strike, right, 'SMART')
    for strike in strikes[:5]
    for right in ['C', 'P']
]

# Qualify and get details
contracts = ib.qualifyContracts(*contracts)

# Request market data
for contract in contracts:
    ticker = ib.reqMktData(contract, '', False, False)
    ib.sleep(1)
    print(f"{contract.right} {contract.strike:7.2f} | Bid: {ticker.bid:6.2f} | Ask: {ticker.ask:6.2f} | IV: {ticker.impliedVolatility:.2%}")

ib.disconnect()
```

---

## 🔧 Troubleshooting {#troubleshooting}

### Connection Issues

**Error 502: Couldn't connect to TWS**
```python
# Solutions:
# 1. Check TWS/Gateway is running
# 2. Check correct port (7497=TWS, 4001=Gateway)
# 3. Enable API in TWS settings
# 4. Check firewall
# 5. Verify clientId is unique

# Test connection
import socket
sock = socket.socket()
try:
    sock.connect(('127.0.0.1', 7497))
    print("Port is open")
except:
    print("Cannot connect to port")
finally:
    sock.close()
```

**Error 326: Unable to connect**
```python
# Check API settings in TWS:
# Configuration -> API -> Settings
# - Enable ActiveX and Socket Clients
# - Socket port: 7497 (TWS) or 4001 (Gateway)
# - Trusted IPs: 127.0.0.1
# - Master API client ID: (optional)
```

### Market Data Issues

**Error 354: Requested market data not subscribed**
```python
# Your account lacks market data subscription
# Options:
# 1. Subscribe to market data in account management
# 2. Use reqMarketDataType(3) for delayed data
# 3. Use reqMarketDataType(4) for frozen delayed

ib.reqMarketDataType(3)  # Delayed data (free)
```

**Missing tick data**
```python
# Don't use waitOnUpdate() loop for ticks - data loss!

# ❌ BAD
while True:
    ib.waitOnUpdate()
    # Some ticks lost!

# ✅ GOOD - Use events
ticker.updateEvent += lambda t: process(t)
```

### Order Issues

**Error 201: Order rejected**
```python
# Common causes:
# 1. Invalid contract
# 2. Insufficient buying power
# 3. Outside trading hours
# 4. Invalid order parameters

# Debug:
orderState = ib.whatIfOrder(contract, order)
print(orderState)
```

**Orders not showing**
```python
# Check:
# 1. Correct clientId
# 2. "Download open orders on connection" enabled in TWS
# 3. Use ib.openOrders() not ib.reqOpenOrders()

# Sync orders
ib.reqOpenOrders()  # Legacy, can be stale
ib.openOrders()     # Better - auto-synced
```

### Historical Data Issues

**Error 162: Historical Market Data Service error**
```python
# Common causes:
# 1. Requesting too much data
# 2. Invalid date range
# 3. Contract not found
# 4. No data available for period

# Solution: Break into chunks
dt = ''
all_bars = []
while True:
    bars = ib.reqHistoricalData(
        contract,
        endDateTime=dt,
        durationStr='30 D',
        barSizeSetting='1 hour',
        whatToShow='TRADES',
        useRTH=True
    )
    if not bars:
        break
    all_bars.extend(bars)
    dt = bars[0].date
    ib.sleep(1)  # Respect rate limits
```

### Performance Issues

**Slow responses**
```python
# Solutions:
# 1. Reduce simultaneous requests
# 2. Use batch requests where possible
# 3. Increase TWS memory allocation
# 4. Use keepUpToDate for live bars instead of repeated requests

# Increase TWS memory:
# Configuration -> Settings -> Memory Allocation -> 4096 MB
```

**Too many requests**
```python
# IB throttles automatically at 45 req/sec
# Monitor throttle events:

def on_throttle_start():
    print("Throttling started")

def on_throttle_end():
    print("Throttling ended")

ib.client.throttleStart += on_throttle_start
ib.client.throttleEnd += on_throttle_end
```

### Jupyter Notebook Issues

**Event loop conflicts**
```python
# At start of notebook:
util.startLoop()

# If still issues:
util.patchAsyncio()

# For old notebooks:
import nest_asyncio
nest_asyncio.apply()
```

### Memory Leaks

**Ticker accumulation**
```python
# Cancel unused tickers
for contract in old_contracts:
    ib.cancelMktData(contract)

# Clear refs
del ticker
```

---

## 📚 Additional Resources

### Official Documentation
- ReadTheDocs: https://ib-insync.readthedocs.io/
- GitHub: https://github.com/erdewit/ib_insync
- IB TWS API: https://interactivebrokers.github.io/tws-api/

### Community
- Discussion Group: https://groups.io/g/insync
- Issues: https://github.com/erdewit/ib_insync/issues

### Key Files to Reference
- `ib_insync/ib.py` - Main IB class
- `ib_insync/contract.py` - Contract types
- `ib_insync/order.py` - Order types
- `ib_insync/ticker.py` - Ticker object
- `ib_insync/objects.py` - Data objects
- `ib_insync/util.py` - Utility functions

---

## 🎓 Summary

### Essential Classes
- `IB()` - Main interface
- `Stock()`, `Forex()`, `Option()`, `Future()` - Contract types
- `MarketOrder()`, `LimitOrder()`, `StopOrder()` - Order types
- `Ticker()` - Real-time market data

### Core Methods
- `connect()` / `disconnect()` - Connection
- `reqMktData()` - Streaming market data
- `reqRealTimeBars()` - Real-time bars
- `reqHistoricalData()` - Historical bars
- `placeOrder()` - Submit orders
- `cancelOrder()` - Cancel orders

### Key Concepts
- Event-driven architecture
- Auto-synced state
- Blocking vs Async methods
- Use `ib.sleep()` not `time.sleep()`
- Stream data, don't poll

### Remember
1. **Real-time feeds** > Historical polling
2. **Events** > Polling loops
3. **Qualify contracts** before use
4. **Never block** event loop
5. **Monitor errors** with errorEvent
6. **Throttling** handled automatically
7. **Clean up** resources on exit

---

**End of ib-insync Complete Reference**
*Last Updated: Based on v0.9.86*