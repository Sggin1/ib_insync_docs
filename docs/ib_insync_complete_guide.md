# ib_insync Python Library: Comprehensive Technical Guide

**The essential guide to Interactive Brokers API integration** using ib_insync v0.9.86+, covering asynchronous programming, state management, order execution, futures contracts, and real-time data streaming. This library simplifies IB's complex native API with a clean Pythonic interface built on asyncio, enabling both blocking and fully asynchronous trading applications.

## Critical library status note

The original ib_insync (v0.9.86) remains functional but is no longer actively developed following its creator Ewald de Wit's passing in March 2024. An actively maintained successor, **ib_async**, continues development under the ib-api-reloaded organization with API compatibility. Both libraries share the same core patterns and this guide applies to both.

---

## Asynchronous programming with ib_insync

ib_insync provides dual interfaces—blocking methods for simple scripts and async methods for advanced applications—all built on Python's asyncio framework. The library's architecture eliminates IB's callback complexity while maintaining full async capabilities for high-performance trading systems.

### The dual interface architecture

Every request method exists in two versions. Blocking methods like `reqHistoricalData()` wait for completion and return results directly. Asynchronous methods like `reqHistoricalDataAsync()` return coroutines for use with `await`. This design lets you choose the appropriate style for each use case.

```python
# Blocking interface - simple and direct
from ib_insync import *

ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)
bars = ib.reqHistoricalData(contract, ...)  # Blocks until complete
```

```python
# Asynchronous interface - non-blocking
import asyncio
from ib_insync import *

async def main():
    ib = IB()
    await ib.connectAsync('127.0.0.1', 7497, clientId=1)
    bars = await ib.reqHistoricalDataAsync(contract, ...)  # Non-blocking
    
asyncio.run(main())
```

### Event loop management patterns

The golden rule: **never use `time.sleep()`**—always use `ib.sleep()`. Blocking Python's sleep freezes the event loop, preventing message processing and causing data accumulation. The ib.sleep() method yields control to the framework, allowing background message handling to continue.

```python
# WRONG - freezes everything
import time
ticker = ib.reqMktData(contract)
time.sleep(5)  # Event loop frozen, no updates processed
print(ticker.last)  # May be empty

# CORRECT - allows message processing
ticker = ib.reqMktData(contract)
ib.sleep(5)  # Framework processes updates in background
print(ticker.last)  # Contains current data
```

For Jupyter notebooks and environments with existing event loops, use `util.startLoop()` or `util.patchAsyncio()` to enable nested event loops via the nest_asyncio package.

```python
# Jupyter notebook setup
from ib_insync import *

util.startLoop()  # Enables nested event loops
ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)
# Can now use blocking methods directly in notebook cells
```

### Long-running applications with continuous event loops

For applications that run indefinitely monitoring markets or managing positions, use the `ib.run()` method to keep the event loop active. Set up event handlers first, then call run() to process events until manually stopped.

```python
from ib_insync import *

ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)

def onTicker(ticker):
    print(f"Price update: {ticker.contract.symbol} @ {ticker.last}")

ticker = ib.reqMktData(contract)
ticker.updateEvent += onTicker

ib.run()  # Runs event loop indefinitely
```

### Event handling in async contexts

ib_insync uses the eventkit library for its event system. Events fire asynchronously and you subscribe using the `+=` operator. Event handlers can be either synchronous functions or async coroutines.

```python
# Synchronous event handler
def onOrderStatus(trade):
    print(f"Order {trade.order.orderId}: {trade.orderStatus.status}")
    if trade.isDone():
        print(f"Filled at: {trade.orderStatus.avgFillPrice}")

ib.orderStatusEvent += onOrderStatus

# Asynchronous event handler
async def onBarUpdate(bars, hasNewBar):
    if hasNewBar:
        print(f"New bar: {bars[-1]}")
        # Can use await inside async handlers
        await ib.qualifyContractsAsync(contract)

bars.updateEvent += onBarUpdate
```

Ticker-specific events provide fine-grained control over individual market data subscriptions:

```python
contract = Forex('EURUSD')
ticker = ib.reqMktData(contract)

async def onTickerUpdate(ticker):
    print(f"EUR/USD: Bid {ticker.bid}, Ask {ticker.ask}")
    
ticker.updateEvent += onTickerUpdate
```

Unsubscribe from events using the `-=` operator, and use the `@event.once` decorator for one-time handlers that automatically unsubscribe after firing.

```python
# Unsubscribe
ticker.updateEvent -= onTickerUpdate

# One-time handler
@ticker.updateEvent.once
def onFirstUpdate(ticker):
    print(f"First update received: {ticker.last}")
```

### Concurrent operations with asyncio

Leverage asyncio.gather() to execute multiple requests concurrently, dramatically reducing total execution time for batch operations.

```python
async def get_multiple_contracts():
    ib = IB()
    await ib.connectAsync('127.0.0.1', 7497, clientId=1)
    
    contracts = [
        Stock('AAPL', 'SMART', 'USD'),
        Stock('GOOGL', 'SMART', 'USD'),
        Stock('MSFT', 'SMART', 'USD')
    ]
    
    # Request all contract details concurrently
    results = await asyncio.gather(*[
        ib.reqContractDetailsAsync(c) for c in contracts
    ])
    
    return results
```

Use asyncio.create_task() for truly concurrent execution of independent operations:

```python
async def monitor_multiple_tickers():
    ib = IB()
    await ib.connectAsync('127.0.0.1', 7497, clientId=1)
    
    async def watch_ticker(contract):
        ticker = ib.reqMktData(contract)
        await ib.sleep(1)
        return ticker
    
    # Create tasks for concurrent execution
    tasks = [
        asyncio.create_task(watch_ticker(Forex('EURUSD'))),
        asyncio.create_task(watch_ticker(Forex('GBPUSD'))),
        asyncio.create_task(watch_ticker(Forex('USDJPY')))
    ]
    
    tickers = await asyncio.gather(*tasks)
    return tickers
```

### Critical async pitfalls to avoid

**Event loop already running**: In Jupyter or event-driven frameworks, you'll encounter this error when trying to use blocking methods. Solution: call `util.patchAsyncio()` before connecting, or use async methods exclusively.

**Blocking callbacks**: Never make blocking calls inside event handlers. Use async versions of methods with await, or schedule the blocking work separately.

```python
# WRONG - blocks event loop in callback
def onBarUpdate(bars, hasNewBar):
    if hasNewBar:
        ib.qualifyContracts(contract)  # Blocking!

# CORRECT - use async handler
async def onBarUpdate(bars, hasNewBar):
    if hasNewBar:
        await ib.qualifyContractsAsync(contract)
```

**Threading issues**: ib_insync uses asyncio and is not thread-safe. If you must use threads, create a new event loop for each thread and call `util.patchAsyncio()` within it.

**Missing tick data with waitOnUpdate()**: The waitOnUpdate() method can miss rapid updates because ticks from the first update get cleared before processing. Always use event handlers for tick data collection.

```python
# WRONG - misses rapid ticks
while True:
    ib.waitOnUpdate()
    print(ticker.last)

# CORRECT - captures all updates
def onTicker(ticker):
    print(ticker.last)
    
ticker.updateEvent += onTicker
```

### Async best practices summary

**Always use ib.sleep()** instead of time.sleep() to prevent event loop blocking. **Yield control periodically** in long-running operations with `ib.sleep(0)`. **Subscribe to events** rather than polling for real-time data. **Use async methods** with asyncio.gather() for concurrent batch operations. **Handle connection errors** with try-except blocks and implement retry logic. **Clean up event subscriptions** by unsubscribing before disconnecting to prevent memory leaks.

---

## Single source of truth implementation

ib_insync implements a single source of truth pattern through its Wrapper class, which automatically synchronizes all application state with the Interactive Brokers API. This architectural choice eliminates manual state management and ensures your application always reflects TWS/Gateway reality.

### The Wrapper as central state container

The IB class provides the user-facing interface, but internally delegates all state storage to the Wrapper. This Wrapper maintains dictionaries for account values, portfolio items, positions, trades, tickers, and all other stateful data. When messages arrive from TWS, the Wrapper updates these internal structures and fires corresponding events.

```python
# Internal architecture (conceptual)
IB Instance
    └── Wrapper Instance (single source of truth)
        ├── accountValues (dict)
        ├── acctSummary (dict)
        ├── portfolio (defaultdict)
        ├── positions (defaultdict)
        ├── trades (dict)
        ├── tickers (dict)
        └── [other state collections]
    └── Client Instance (network communication)
```

All IB methods that return state—`positions()`, `portfolio()`, `orders()`, `trades()`—query the Wrapper's current state. These objects are live-updated in the background as messages arrive, meaning every access reflects the latest known state.

### Always access fresh state, never cache

The critical pattern: **never store copies of state in long-lived variables**. Always call IB methods to access current state. Stored copies become stale as the Wrapper updates in the background.

```python
# CORRECT - access live state
def check_positions():
    positions = ib.positions()
    for pos in positions:
        print(f"{pos.contract.symbol}: {pos.position}")

# WRONG - storing stale copies
cached_positions = ib.positions()  # Snapshot becomes stale
# Later...
print(cached_positions)  # Likely outdated
```

The returned objects themselves—Ticker, Trade, Position, Portfolio—are live references that the framework updates automatically. A Ticker object from reqMktData() continuously updates its bid, ask, and last prices. A Trade object from placeOrder() updates its orderStatus as the order progresses through its lifecycle.

```python
# Trade object is automatically updated
order = LimitOrder('BUY', 100, 150.0)
trade = ib.placeOrder(contract, order)

# trade.orderStatus updates automatically in background
def check_order_status():
    if trade.orderStatus.status == 'Filled':
        print("Order filled!")
    elif trade.isDone():
        print("Order completed")
```

### Event-driven updates for real-time monitoring

Use events for real-time updates rather than polling. The framework fires events whenever state changes, allowing immediate reaction without constant checking.

```python
def onPositionUpdate(position):
    print(f"Position: {position.contract.symbol}: {position.position}")

ib.positionEvent += onPositionUpdate

def onPortfolioUpdate(item):
    print(f"P&L: {item.contract.symbol}, Unrealized: {item.unrealizedPNL}")

ib.updatePortfolioEvent += onPortfolioUpdate
```

The global `updateEvent` fires on any state change, useful for triggering comprehensive checks:

```python
def onUpdate():
    positions = ib.positions()
    print(f"Current positions: {len(positions)}")

ib.updateEvent += onUpdate
```

### Yielding control in long operations

When performing calculations or processing that takes significant time, yield control to the event loop periodically using `ib.sleep(0)`. This allows the Wrapper to process incoming messages and update state during your operation.

```python
def long_calculation():
    for i in range(1000):
        result = expensive_operation()
        
        # Periodically yield to allow state updates
        if i % 100 == 0:
            ib.sleep(0)
        
        # State may have changed during sleep
        current_positions = ib.positions()
```

### Patterns for accessing portfolio and positions

```python
# All portfolio items across accounts
all_portfolio = ib.portfolio()

# Portfolio for specific account
account_portfolio = ib.portfolio(account='U1234567')

# All positions
all_positions = ib.positions()

# Positions for specific account
account_positions = ib.positions(account='U1234567')

# Iterate through positions
for position in ib.positions():
    symbol = position.contract.symbol
    qty = position.position
    avg_cost = position.avgCost
    print(f"{symbol}: {qty} @ ${avg_cost}")
```

### Trade and order management state

```python
# Get all open orders
open_orders = ib.orders()

# Get all trades (open and completed from this session)
all_trades = ib.trades()

# Get all fills from this session
fills = ib.fills()

# Request all open orders including from other clients
ib.reqAllOpenOrders()
```

### Thread safety and concurrency

ib_insync uses asyncio and is **not thread-safe**. All operations should occur on the main event loop thread. Use asyncio tasks for concurrency within the event loop, not traditional threading.

```python
# WRONG - threading with asyncio
from concurrent.futures import ThreadPoolExecutor
executor = ThreadPoolExecutor(max_workers=2)
executor.submit(ib.positions)  # Will fail!

# CORRECT - use asyncio tasks
async def fetch_multiple_contracts():
    tasks = [
        ib.qualifyContractsAsync(contract1),
        ib.qualifyContractsAsync(contract2),
        ib.qualifyContractsAsync(contract3)
    ]
    results = await asyncio.gather(*tasks)
    return results
```

### Common anti-patterns and mistakes

**Mutating returned objects**: Don't modify objects returned by ib_insync. Treat them as read-only views of state.

**Caching with incorrect invalidation**: If you must cache state for performance, implement short-lived caching with explicit refresh logic.

```python
class TradingBot:
    def __init__(self, ib):
        self.ib = ib
        self._positions_cache = None
        self._cache_time = None
        
    def get_positions(self, max_age=1.0):
        """Get positions with short-term caching"""
        now = time.time()
        if (self._positions_cache is None or 
            self._cache_time is None or 
            now - self._cache_time > max_age):
            self._positions_cache = self.ib.positions()
            self._cache_time = now
        return self._positions_cache
```

**Not checking connection state**: Always verify connection before state access.

```python
def get_price():
    if not ib.isConnected():
        raise ConnectionError("Not connected to IB")
    ticker = ib.reqMktData(contract)
    ib.sleep(2)
    if ticker.last:
        return ticker.last
    raise ValueError("No price data available")
```

### Production-ready state manager

```python
from ib_insync import *
import logging

class IBDataManager:
    """Demonstrates best practices for single source of truth pattern"""
    
    def __init__(self, host='127.0.0.1', port=7497, client_id=1):
        self.ib = IB()
        self.host = host
        self.port = port
        self.client_id = client_id
        self._setup_logging()
        self._setup_events()
    
    def _setup_logging(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _setup_events(self):
        self.ib.connectedEvent += self._on_connected
        self.ib.disconnectedEvent += self._on_disconnected
        self.ib.positionEvent += self._on_position
        self.ib.updatePortfolioEvent += self._on_portfolio
    
    def connect(self):
        try:
            self.ib.connect(self.host, self.port, clientId=self.client_id)
            self.logger.info("Connected to IB")
            return True
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            return False
    
    def _on_connected(self):
        self.logger.info("Connection established")
        self.ib.reqAccountSummary()
    
    def _on_disconnected(self):
        self.logger.warning("Disconnected from IB")
    
    def _on_position(self, position):
        self.logger.info(f"Position update: {position.contract.symbol}")
    
    def _on_portfolio(self, item):
        self.logger.info(f"Portfolio update: {item.contract.symbol}")
    
    def get_current_positions(self):
        """Get current positions (always fresh from single source)"""
        if not self.ib.isConnected():
            raise ConnectionError("Not connected")
        return self.ib.positions()
    
    def get_position_for_symbol(self, symbol):
        """Get position for specific symbol"""
        for pos in self.get_current_positions():
            if pos.contract.symbol == symbol:
                return pos
        return None
```

---

## Order placement: Complete patterns and examples

ib_insync simplifies order placement while supporting all Interactive Brokers order types. This section covers market orders, limit orders, trailing stops, OCO orders, bracket orders, and complex combinations with production-ready code patterns.

### Market orders

Market orders execute immediately at the current market price with no price protection. They're the simplest order type but carry slippage risk in volatile markets.

```python
from ib_insync import *

ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)

# Create and qualify contract
contract = Stock('AAPL', 'SMART', 'USD')
ib.qualifyContracts(contract)

# Create and place market order
order = MarketOrder('BUY', 100)
trade = ib.placeOrder(contract, order)

# Monitor order status
print(f"Order status: {trade.orderStatus.status}")
```

Market orders often execute so quickly that intermediate status callbacks are skipped. Always monitor execDetails events rather than relying solely on orderStatus for market orders.

```python
def order_status_callback(trade):
    if trade.orderStatus.status == 'Filled':
        fill = trade.fills[-1]
        print(f'{fill.time} - {fill.execution.side} {fill.contract.symbol} '
              f'{fill.execution.shares} @ {fill.execution.avgPrice}')

trade.filledEvent += order_status_callback
```

### Limit orders

Limit orders execute only at the specified price or better, providing price protection but no guarantee of execution. Set time-in-force parameters to control order lifespan.

```python
# Basic limit order
limit_order = LimitOrder('BUY', 100, 150.00)
trade = ib.placeOrder(contract, limit_order)

# Limit order with time-in-force
limit_order = LimitOrder('BUY', 100, 150.00)
limit_order.tif = 'GTD'  # Good Till Date
limit_order.goodTillDate = '20240331 23:59:59'
trade = ib.placeOrder(contract, limit_order)

# Allow outside regular trading hours
limit_order = LimitOrder('BUY', 100, 150.00)
limit_order.outsideRth = True
trade = ib.placeOrder(contract, limit_order)
```

Time-in-force options: `DAY` (default, expires end of day), `GTC` (Good Till Cancelled, persists across sessions), `GTD` (Good Till Date, expires at specified time), `IOC` (Immediate or Cancel), `FOK` (Fill or Kill).

**Critical**: GTC orders persist across sessions and can result in unexpected fills days later. Always track open orders and cancel when no longer needed.

### Trailing stop orders

Trailing stops follow favorable price movement, maintaining a specified distance from the highest price reached (for sells) or lowest price (for buys). They protect profits while allowing continued upside.

```python
# Trailing stop with fixed dollar amount
trailing_order = Order()
trailing_order.action = 'SELL'
trailing_order.orderType = 'TRAIL'
trailing_order.totalQuantity = 100
trailing_order.auxPrice = 2.0  # Trail by $2
trailing_order.trailStopPrice = 150.0  # Initial trigger price

trade = ib.placeOrder(contract, trailing_order)

# Trailing stop with percentage
trailing_order = Order()
trailing_order.action = 'SELL'
trailing_order.orderType = 'TRAIL'
trailing_order.totalQuantity = 100
trailing_order.trailingPercent = 5.0  # Trail by 5%

trade = ib.placeOrder(contract, trailing_order)
```

Trailing stop limit orders trigger a limit order (rather than market order) when the stop is hit, providing more control but risking non-execution:

```python
trail_limit_order = Order()
trail_limit_order.orderType = 'TRAIL LIMIT'
trail_limit_order.totalQuantity = 100
trail_limit_order.action = 'SELL'
trail_limit_order.lmtPriceOffset = 0.5  # Limit price offset from stop
trail_limit_order.auxPrice = 2.0  # Trail amount
trail_limit_order.trailStopPrice = 150.0

trade = ib.placeOrder(contract, trail_limit_order)
```

**Known issue**: On Windows, TRAIL LIMIT orders may fail if both lmtPrice and lmtPriceOffset are set. Use only lmtPriceOffset, not lmtPrice.

### OCO (One-Cancels-Other) orders

OCO orders link multiple orders such that when one executes, the others automatically cancel. Use for scenarios like placing buy orders at multiple price levels where you only want one fill.

```python
# Using the helper method (recommended)
orders = [
    LimitOrder('BUY', 100, 150.00),
    LimitOrder('BUY', 100, 149.00),
    LimitOrder('BUY', 100, 148.00)
]

oca_orders = ib.oneCancelsAll(orders, 'TestOCA_123', 2)

for order in oca_orders:
    ib.placeOrder(contract, order)
```

Manual OCO setup provides more control over individual order parameters:

```python
oca_group_name = 'MyOCAGroup_123'

order1 = LimitOrder('BUY', 100, 150.00)
order1.ocaGroup = oca_group_name
order1.ocaType = 2  # Proportional reduction with block
order1.transmit = False

order2 = LimitOrder('BUY', 100, 149.00)
order2.ocaGroup = oca_group_name
order2.ocaType = 2
order2.transmit = False

order3 = LimitOrder('BUY', 100, 148.00)
order3.ocaGroup = oca_group_name
order3.ocaType = 2
order3.transmit = True  # Last order triggers transmission

ib.placeOrder(contract, order1)
ib.placeOrder(contract, order2)
ib.placeOrder(contract, order3)
```

The ocaType parameter controls cancellation behavior: `1` (cancel all with block), `2` (proportional reduction with block, **recommended**), `3` (proportional reduction without block, risks overfill).

**Critical**: Use unique OCA group names including timestamp or order ID to prevent conflicts. Set `transmit=False` on all orders except the last to prevent premature execution.

### Bracket orders

Bracket orders combine an entry order with both profit target and stop loss orders, providing complete position management in a single atomic operation. The children (profit and stop) only activate after the parent order fills.

```python
# Using the helper function (recommended)
bracket = ib.bracketOrder(
    'BUY',
    quantity=100,
    limitPrice=150.00,
    takeProfitPrice=155.00,
    stopLossPrice=145.00
)

for order in bracket:
    ib.placeOrder(contract, order)
```

For market entry instead of limit entry, modify the parent order:

```python
bracket = ib.bracketOrder('BUY', 100, 150.00, 155.00, 145.00)
bracket[0].orderType = 'MKT'
bracket[0].lmtPrice = 0

for order in bracket:
    ib.placeOrder(contract, order)
```

Manual bracket construction for full control:

```python
parent = Order()
parent.orderId = ib.client.getReqId()
parent.action = 'BUY'
parent.orderType = 'LMT'
parent.totalQuantity = 100
parent.lmtPrice = 150.00
parent.transmit = False

takeProfit = Order()
takeProfit.orderId = parent.orderId + 1
takeProfit.action = 'SELL'
takeProfit.orderType = 'LMT'
takeProfit.totalQuantity = 100
takeProfit.lmtPrice = 155.00
takeProfit.parentId = parent.orderId
takeProfit.transmit = False

stopLoss = Order()
stopLoss.orderId = parent.orderId + 2
stopLoss.action = 'SELL'
stopLoss.orderType = 'STP'
stopLoss.auxPrice = 145.00
stopLoss.totalQuantity = 100
stopLoss.parentId = parent.orderId
stopLoss.transmit = True  # Last order triggers all

ib.placeOrder(contract, parent)
ib.placeOrder(contract, takeProfit)
ib.placeOrder(contract, stopLoss)
```

**Critical transmit flag pattern**: Set `transmit=False` on parent and all children except the last. Only the final child should have `transmit=True`, triggering atomic submission of the entire group.

### Bracket with multiple profit targets

Scale out of positions by setting multiple take-profit levels:

```python
from typing import NamedTuple

class BracketOrderTwoTargets(NamedTuple):
    parent: Order
    takeProfit1: Order
    takeProfit2: Order
    stopLoss: Order

def bracket_two_targets(action, quantity, limit_price, 
                       tp_price1, tp_price2, sl_price, ib):
    """Create bracket with two take-profit targets"""
    
    parent = LimitOrder(action, quantity, limit_price)
    parent.orderId = ib.client.getReqId()
    parent.transmit = False
    
    # First take profit (half position)
    takeProfit1 = LimitOrder(
        'SELL' if action == 'BUY' else 'BUY',
        quantity // 2,
        tp_price1
    )
    takeProfit1.orderId = parent.orderId + 1
    takeProfit1.parentId = parent.orderId
    takeProfit1.transmit = False
    
    # Second take profit (remaining half)
    takeProfit2 = LimitOrder(
        'SELL' if action == 'BUY' else 'BUY',
        quantity // 2,
        tp_price2
    )
    takeProfit2.orderId = parent.orderId + 2
    takeProfit2.parentId = parent.orderId
    takeProfit2.transmit = False
    
    # Stop loss for full position
    stopLoss = StopOrder(
        'SELL' if action == 'BUY' else 'BUY',
        quantity,
        sl_price
    )
    stopLoss.orderId = parent.orderId + 3
    stopLoss.parentId = parent.orderId
    stopLoss.transmit = True
    
    return BracketOrderTwoTargets(parent, takeProfit1, takeProfit2, stopLoss)

# Usage
bracket = bracket_two_targets('BUY', 200, 150.00, 155.00, 160.00, 145.00, ib)
for order in bracket:
    ib.placeOrder(contract, order)
```

### Dynamic bracket based on fill price

For strategies requiring exact profit/loss ratios based on actual fill price, place the entry order first, then calculate and submit bracket orders:

```python
contract = Forex('GBPUSD')
ib.qualifyContracts(contract)

# Place entry order
parent_order = MarketOrder('BUY', 25000)
trade = ib.placeOrder(contract, parent_order)

# Wait for fill
ib.sleep(1)
while trade.orderStatus.status != 'Filled':
    ib.waitOnUpdate()

# Calculate levels based on actual fill price
fill_price = trade.orderStatus.avgFillPrice
stop_loss_price = fill_price - 0.0015
take_profit_price = fill_price + 0.0020

# Place child orders
stop_loss_order = StopOrder('SELL', 25000, stop_loss_price)
take_profit_order = LimitOrder('SELL', 25000, take_profit_price)

ib.placeOrder(contract, stop_loss_order)
ib.placeOrder(contract, take_profit_order)
```

### Order status monitoring

```python
# Trade object attributes
trade.order          # The original order
trade.orderStatus    # Current status object
trade.fills          # List of fills
trade.log            # Log of status changes
trade.isActive()     # Is order still active
trade.isDone()       # Is order complete

# Order status values
# PendingSubmit, PendingCancel, PreSubmitted, Submitted, 
# Filled, Cancelled, Inactive, ApiPending

# Event callbacks for monitoring
def on_fill(trade, fill):
    print(f'Filled {fill.execution.shares} @ {fill.execution.price}')

trade.fillEvent += on_fill

def on_filled(trade):
    total = sum(f.execution.shares for f in trade.fills)
    avg_price = trade.orderStatus.avgFillPrice
    print(f'Complete: {total} shares @ avg {avg_price}')

trade.filledEvent += on_filled

def on_status(trade):
    print(f'Status: {trade.orderStatus.status}')

trade.statusEvent += on_status
```

### Order placement best practices

**Always qualify contracts** before placing orders to ensure all required fields are populated. **Save the trade object** returned by placeOrder() for status monitoring. **Use callbacks** for asynchronous monitoring rather than blocking loops. **Test in paper account** before live trading. **Monitor both orderStatus and execDetails** since market orders may skip status updates. **Handle partial fills** appropriately by checking remaining quantity. **Cancel GTC orders** when no longer needed to prevent unexpected fills.

---

## Contract qualification for futures

Contract qualification fills in missing contract details by querying Interactive Brokers' servers. For futures contracts, proper qualification is essential before placing orders or requesting market data. This section covers futures-specific patterns, handling expiries, and rollover strategies.

### Creating futures contracts

The Future class provides the cleanest syntax for futures contracts:

```python
from ib_insync import *

ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)

# Recommended method
contract = Future('ES', '202506', 'CME')

# With additional parameters
contract = Future(
    symbol='ES',
    lastTradeDateOrContractMonth='202506',
    exchange='CME',
    localSymbol='ESM6',
    multiplier='50',
    currency='USD'
)
```

The generic Contract class requires more verbose setup:

```python
contract = Contract()
contract.secType = 'FUT'
contract.symbol = 'MNQ'
contract.exchange = 'CME'
contract.currency = 'USD'
contract.localSymbol = 'MNQZ5'
```

Using conId (contract identifier) provides the most precise identification when known:

```python
contract = Contract(conId=495512516)
```

### Required and optional fields for futures

**Required**: symbol (futures root like 'ES', 'NQ', 'CL'), secType ('FUT'), exchange (destination exchange like 'CME', 'NYMEX', 'CBOT').

**Recommended**: lastTradeDateOrContractMonth (format YYYYMM for contract month or YYYYMMDD for specific expiry), localSymbol (IB's symbol like 'ESH3'), multiplier (contract multiplier), currency (typically 'USD').

**Special**: includeExpired (boolean for accessing expired futures data, up to 2 years), conId (unique IB identifier, most precise when known).

### Correct exchange specifications

| Product | Correct Exchange | Incorrect/Outdated Exchange |
|---------|------------------|----------------------------|
| ES, NQ, MES, MNQ | CME | GLOBEX |
| CL, GC, SI | NYMEX | GLOBEX |
| ZB, ZN, ZF | CBOT | ECBOT |
| 6E, 6A, 6B | CME | GLOBEX |

### The qualifyContracts method

Qualification sends a contract details request to IB servers, fills in missing fields (especially conId, localSymbol, multiplier, exact expiry date, tradingClass), and returns a list of successfully qualified contracts. It logs warnings for unknown or ambiguous contracts.

```python
# Single contract
contract = Future('ES', '202506', 'CME')
qualified = ib.qualifyContracts(contract)

# Multiple contracts concurrently
contracts = [
    Future('ES', '202506', 'CME'),
    Future('NQ', '202506', 'CME'),
    Future('CL', '202506', 'NYMEX')
]
qualified = ib.qualifyContracts(*contracts)
```

The method updates the contract object in-place when successful:

```python
contract = Future('ES', '202506', 'CME')
qualified = ib.qualifyContracts(contract)

if qualified:
    contract = qualified[0]
    print(f"ConId: {contract.conId}")
    print(f"Local Symbol: {contract.localSymbol}")
    print(f"Expiry: {contract.lastTradeDateOrContractMonth}")
```

### Handling ambiguous contracts

When multiple contracts match your specification, qualifyContracts() logs a warning with possible matches. The solution: be more specific with contract details.

```python
# Too vague - multiple matches
contract = Future('ES', exchange='CME')
ib.qualifyContracts(contract)
# Warning: Ambiguous contract, possibles are [Future('ES', '202506'), ...]

# Specific - unambiguous
contract = Future('ES', '202506', 'CME')
ib.qualifyContracts(contract)  # Success

# Or use localSymbol
contract = Future('ES', exchange='CME', localSymbol='ESM6')
ib.qualifyContracts(contract)  # Success

# Or use conId (most precise)
contract = Contract(conId=495512516)
ib.qualifyContracts(contract)  # Always unambiguous
```

### Validation before trading

Always validate and handle qualification failures before placing orders:

```python
def validate_futures_contract(ib, contract):
    """Validate and qualify a futures contract"""
    try:
        qualified = ib.qualifyContracts(contract)
        if not qualified:
            print(f"ERROR: Contract could not be qualified")
            return None
        
        contract = qualified[0]
        print(f"✓ Qualified: {contract.localSymbol}")
        print(f"  ConId: {contract.conId}")
        print(f"  Expiry: {contract.lastTradeDateOrContractMonth}")
        return contract
    except Exception as e:
        print(f"ERROR: {e}")
        return None

# Usage
contract = Future('ES', '202506', 'CME')
validated = validate_futures_contract(ib, contract)
if validated:
    order = MarketOrder('BUY', 1)
    trade = ib.placeOrder(validated, order)
```

### Contract detail retrieval

Use reqContractDetails() to get comprehensive contract information beyond basic qualification:

```python
contract = Future('ES', '202506', 'CME')
details_list = ib.reqContractDetails(contract)

for details in details_list:
    print(f"ConId: {details.contract.conId}")
    print(f"Local Symbol: {details.contract.localSymbol}")
    print(f"Expiry: {details.contract.lastTradeDateOrContractMonth}")
    print(f"Multiplier: {details.contract.multiplier}")
    print(f"Min Tick: {details.minTick}")
    print(f"Market Name: {details.marketName}")
```

### Handling expired contracts

The includeExpired flag enables access to expired futures data for up to 2 years after expiration. This works only for historical data requests and contract details, not for real-time data or order placement.

```python
# Request data for expired contract
contract = Future('ES', '202012', 'CME')
contract.includeExpired = True

qualified = ib.qualifyContracts(contract)
if qualified:
    bars = ib.reqHistoricalData(
        qualified[0],
        endDateTime='',
        durationStr='1 Y',
        barSizeSetting='1 day',
        whatToShow='TRADES',
        useRTH=True
    )
    print(f"Retrieved {len(bars)} bars")
```

### Futures rollover strategies

Implement automatic front month detection to handle contract rollovers:

```python
from datetime import datetime

def get_front_month_contract(ib, symbol, exchange):
    """Get the front month futures contract"""
    contract = Future(symbol, exchange=exchange)
    contract_details = ib.reqContractDetails(contract)
    
    if not contract_details:
        return None
    
    now = datetime.now()
    active_contracts = []
    
    for details in contract_details:
        expiry_str = details.contract.lastTradeDateOrContractMonth
        if len(expiry_str) == 8:
            expiry = datetime.strptime(expiry_str, '%Y%m%d')
        else:
            expiry = datetime.strptime(expiry_str, '%Y%m')
        
        if expiry > now:
            active_contracts.append((expiry, details.contract))
    
    if not active_contracts:
        return None
    
    # Sort and return front month
    active_contracts.sort(key=lambda x: x[0])
    front_month = active_contracts[0][1]
    
    qualified = ib.qualifyContracts(front_month)
    return qualified[0] if qualified else None

# Usage
es_front = get_front_month_contract(ib, 'ES', 'CME')
print(f"Front month: {es_front.localSymbol}")
```

Check if rollover is needed based on days to expiry:

```python
def check_rollover_needed(contract, days_before=5):
    """Check if rollover needed"""
    expiry_str = contract.lastTradeDateOrContractMonth
    if len(expiry_str) == 8:
        expiry = datetime.strptime(expiry_str, '%Y%m%d')
    else:
        expiry = datetime.strptime(expiry_str + '01', '%Y%m%d')
    
    days_to_expiry = (expiry - datetime.now()).days
    return days_to_expiry <= days_before
```

### Continuous futures limitations

ContFuture provides rolled contract data for backtesting but has significant limitations:

```python
# Continuous futures (historical data only)
cont_future = ContFuture('ES', 'CME')
ib.qualifyContracts(cont_future)

bars = ib.reqHistoricalData(
    cont_future,
    endDateTime='',
    durationStr='2 Y',
    barSizeSetting='1 day',
    whatToShow='TRADES',
    useRTH=True
)
```

**Critical limitations**: Available from TWS v971+ only. **Cannot be used for real-time data**. **Cannot be used to place orders**. Only for historical data requests.

### Contract qualification best practices

**Always qualify before trading** to ensure all required fields are populated. **Use specific identifiers** (localSymbol, exact expiry date, or conId) to avoid ambiguity. **Handle qualification failures** gracefully with proper error checking. **Validate contract details** before order placement. **Use appropriate date formats** (YYYYMM for month, YYYYMMDD for specific date). **Verify the exchange** as different products trade on different exchanges (CME vs NYMEX vs CBOT). **Monitor expiries** and implement rollover logic for continuous trading. **Use includeExpired=True** only for historical data on expired contracts.

### Common futures mistakes

**Not qualifying before use**: Always call qualifyContracts() before placing orders or requesting data.

**Wrong exchange**: ES trades on CME, not GLOBEX. CL trades on NYMEX. Check exchange for each product.

**Mixing date formats**: Be consistent with YYYYMM (contract month) vs YYYYMMDD (specific date).

**Expired contracts without flag**: Set includeExpired=True for historical data on expired contracts.

**Trading on continuous futures**: ContFuture is only for historical data, never for orders or real-time data.

**Missing secType**: When using generic Contract class, always set secType='FUT'.

---

## Live data stream handling

ib_insync provides multiple methods for streaming real-time market data, each optimized for different use cases. Understanding subscription methods, event-driven processing, and performance patterns enables building robust, efficient trading systems.

### Market data streaming with reqMktData

The most common method for real-time tick data, reqMktData() subscribes to continuous price updates for a contract:

```python
from ib_insync import *

ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)

contract = Stock('AAPL', 'SMART', 'USD')
ib.qualifyContracts(contract)

# Subscribe to market data
ticker = ib.reqMktData(contract, '', False, False)

# Wait for data to populate
ib.sleep(2)

# Access real-time data
print(f"Last: {ticker.last}, Bid: {ticker.bid}, Ask: {ticker.ask}")
```

The genericTickList parameter requests specific data fields using tick IDs: `100` (options volume), `101` (options open interest), `106` (implied volatility), `165` (52-week high/low), `233` (time & sales with last, lastSize, rtVolume, rtTime, vwap), `456` (dividends).

```python
# Request time & sales data
ticker = ib.reqMktData(contract, '233', False, False)
ib.sleep(2)
print(f"VWAP: {ticker.vwap}, Volume: {ticker.rtVolume}")
```

### Real-time bars with reqRealTimeBars

Provides 5-second aggregated bars, the only bar size supported by Interactive Brokers for real-time bar streaming:

```python
contract = Forex('EURUSD')

# Request 5-second bars
bars = ib.reqRealTimeBars(
    contract,
    5,              # Bar size (only 5 seconds supported)
    'MIDPOINT',     # Can be TRADES, MIDPOINT, BID, or ASK
    False           # useRTH
)

# Access bars list
print(bars[-1])  # Most recent bar
```

### Streaming historical bars

Historical bars with keepUpToDate=True continue updating in real-time after the initial historical data loads:

```python
contract = Stock('TSLA', 'SMART', 'USD')

bars = ib.reqHistoricalData(
    contract,
    endDateTime='',
    durationStr='1 D',
    barSizeSetting='1 min',
    whatToShow='TRADES',
    useRTH=True,
    formatDate=1,
    keepUpToDate=True  # Enables live updates
)

# Bars continue updating automatically
```

### Tick-by-tick data

The most granular data stream, providing every individual tick from the exchange. Limited to 3 simultaneous subscriptions per client:

```python
contract = Forex('EURUSD')

ticker = ib.reqTickByTickData(
    contract,
    'BidAsk',  # Can be Last, AllLast, BidAsk, or MidPoint
    0,         # numberOfTicks (0 = unlimited)
    False      # ignoreSize
)

# Access tick-by-tick data
print(ticker.tickByTicks)
```

### Market depth streaming

Order book (Level II) data showing bid and ask depth. Requires Level II market data subscription:

```python
contract = Forex('EURUSD')

ticker = ib.reqMktDepth(contract)
ib.sleep(2)

# Access order book
print("Bids:", [(d.price, d.size) for d in ticker.domBids[:5]])
print("Asks:", [(d.price, d.size) for d in ticker.domAsks[:5]])
```

### Event-driven data processing

The most efficient pattern for processing real-time data uses event handlers that fire automatically when new data arrives.

**Individual ticker events** for ticker-specific logic:

```python
def onTickerUpdate(ticker):
    print(f"{ticker.contract.symbol}: Last {ticker.last}")

contract = Stock('AAPL', 'SMART', 'USD')
ticker = ib.reqMktData(contract)
ticker.updateEvent += onTickerUpdate

ib.run()
```

**Global pendingTickersEvent** for monitoring multiple tickers efficiently:

```python
contracts = [
    Stock('AAPL', 'SMART', 'USD'),
    Stock('GOOGL', 'SMART', 'USD'),
    Stock('MSFT', 'SMART', 'USD')
]

ib.qualifyContracts(*contracts)
tickers = [ib.reqMktData(c) for c in contracts]

def onPendingTickers(tickers):
    """Called when any subscribed ticker has new data"""
    for ticker in tickers:
        print(f"{ticker.contract.symbol}: {ticker.last}")

ib.pendingTickersEvent += onPendingTickers
ib.run()
```

**Bar update events** for streaming bar data:

```python
def onBarUpdate(bars, hasNewBar):
    """
    bars: BarDataList containing all bars
    hasNewBar: Boolean indicating if a new bar was added
    """
    if hasNewBar:
        latest = bars[-1]
        print(f"New bar: O={latest.open}, H={latest.high}, "
              f"L={latest.low}, C={latest.close}")

bars = ib.reqRealTimeBars(contract, 5, 'MIDPOINT', False)
bars.updateEvent += onBarUpdate
ib.run()
```

### Processing multiple tickers with pandas

Combine ib_insync with pandas for structured data handling:

```python
import pandas as pd

contracts = [Forex(pair) for pair in ('EURUSD', 'GBPUSD', 'USDJPY')]
ib.qualifyContracts(*contracts)
tickers = [ib.reqMktData(c) for c in contracts]

# Create DataFrame
df = pd.DataFrame(
    index=[c.pair() for c in contracts],
    columns=['bidSize', 'bid', 'ask', 'askSize', 'high', 'low', 'close']
)

def onPendingTickers(tickers):
    for t in tickers:
        df.loc[t.contract.pair()] = (
            t.bidSize, t.bid, t.ask, t.askSize, 
            t.high, t.low, t.close
        )
    print(df)

ib.pendingTickersEvent += onPendingTickers
ib.sleep(30)
```

### The critical rule: never block the event loop

**Never use time.sleep()** in callbacks or main code—it freezes the event loop and prevents message processing. Always use ib.sleep() to yield control.

```python
# WRONG - blocks everything
import time

def onTickerUpdate(ticker):
    time.sleep(5)  # Frozen!
    process(ticker)

# CORRECT - yields control
def onTickerUpdate(ticker):
    ib.sleep(0)  # Yields to allow message processing
    process(ticker)
```

For long-running operations, yield control periodically:

```python
def onTickerUpdate(ticker):
    for i in range(1000):
        process_chunk(i)
        if i % 100 == 0:
            ib.sleep(0)  # Yield every 100 iterations
```

### Request throttling and memory management

ib_insync automatically throttles requests to 45 requests per second, compatible with TWS/Gateway 974+. No manual intervention needed for individual requests, but spread out batch operations:

```python
for contract in large_contract_list:
    ticker = ib.reqMktData(contract)
    ib.sleep(0.02)  # Small delay between requests
```

**Critical memory setting**: In TWS/Gateway settings, increase Java memory allocation to **4096 MB minimum** to prevent crashes during bulk data operations.

### Managing subscription limits

Interactive Brokers limits concurrent subscriptions: typically 100 for market data lines, only 3 for tick-by-tick data.

```python
active_subscriptions = set()
MAX_SUBSCRIPTIONS = 95  # Leave margin

def subscribe_with_limit(contract):
    if len(active_subscriptions) >= MAX_SUBSCRIPTIONS:
        # Unsubscribe oldest
        oldest = active_subscriptions.pop()
        ib.cancelMktData(oldest)
    
    ticker = ib.reqMktData(contract)
    active_subscriptions.add(contract)
    return ticker
```

### Ticker manager pattern

Encapsulate subscription management in a reusable class:

```python
class TickerManager:
    def __init__(self, ib):
        self.ib = ib
        self.tickers = {}
        self.contracts = {}
        
    def subscribe(self, symbol, exchange='SMART', currency='USD'):
        contract = Stock(symbol, exchange, currency)
        self.ib.qualifyContracts(contract)
        
        ticker = self.ib.reqMktData(contract)
        ticker.updateEvent += self.onUpdate
        
        self.tickers[symbol] = ticker
        self.contracts[symbol] = contract
        return ticker
    
    def unsubscribe(self, symbol):
        if symbol in self.tickers:
            self.ib.cancelMktData(self.contracts[symbol])
            del self.tickers[symbol]
            del self.contracts[symbol]
    
    def onUpdate(self, ticker):
        symbol = ticker.contract.symbol
        print(f"{symbol}: {ticker.last}")

# Usage
manager = TickerManager(ib)
manager.subscribe('AAPL')
manager.subscribe('GOOGL')
```

### Properly unsubscribing and cleanup

**Critical**: Use the same contract object for cancellation that you used for subscription. Creating a new identical contract won't work—object identity matters.

```python
# WRONG
contract1 = Stock('AAPL', 'SMART', 'USD')
ticker = ib.reqMktData(contract1)

contract2 = Stock('AAPL', 'SMART', 'USD')  # Different object!
ib.cancelMktData(contract2)  # Won't work

# CORRECT
contract = Stock('AAPL', 'SMART', 'USD')
ticker = ib.reqMktData(contract)
ib.cancelMktData(contract)  # Use same object
```

Cancel different data types with specific methods:

```python
ib.cancelMktData(contract)
ib.cancelRealTimeBars(bars)
ib.cancelHistoricalData(bars)
ib.cancelTickByTickData(contract, 'BidAsk')
ib.cancelMktDepth(contract)
```

Remove event handlers before unsubscribing to prevent memory leaks:

```python
ticker.updateEvent += handler
# Later...
ticker.updateEvent -= handler
ib.cancelMktData(contract)
```

Proper shutdown procedure:

```python
def shutdown():
    # Cancel all subscriptions
    for contract in active_contracts:
        ib.cancelMktData(contract)
    
    # Allow cancellations to process
    ib.sleep(1)
    
    # Disconnect
    ib.disconnect()

try:
    ib.run()
finally:
    shutdown()
```

### Common mistakes causing data loss

**Wrong contract object for cancellation**: Must use the same object instance used for subscription.

**Blocking in callbacks**: Using time.sleep() freezes message processing.

**Not processing ticks immediately**: The ticker.ticks list is automatically cleared after each update—process ticks in event handlers when they arrive.

```python
# WRONG - ticks cleared before checking
ticker = ib.reqMktData(contract)
ib.sleep(5)
print(ticker.ticks)  # Likely empty

# CORRECT - process in event
def onUpdate(ticker):
    for tick in ticker.ticks:
        process_tick(tick)

ticker.updateEvent += onUpdate
```

**Accumulating historical bars**: When using keepUpToDate=True, limit buffer size to prevent unbounded memory growth.

```python
def onBarUpdate(bars, hasNewBar):
    if len(bars) > 1000:
        # Keep only last 1000 bars
        del bars[:len(bars)-1000]
```

**Not removing event handlers**: Handlers remain attached even after unsubscribing, causing memory leaks. Always remove handlers before canceling subscriptions.

### Production-ready streaming system

```python
from ib_insync import *
import logging

logging.basicConfig(level=logging.INFO)

class TradingSystem:
    def __init__(self):
        self.ib = IB()
        self.tickers = {}
        self.active_contracts = set()
        
    def connect(self):
        self.ib.connect('127.0.0.1', 7497, clientId=1)
        self.ib.errorEvent += self.onError
        self.ib.pendingTickersEvent += self.onPendingTickers
        
    def subscribe(self, symbol):
        contract = Stock(symbol, 'SMART', 'USD')
        self.ib.qualifyContracts(contract)
        
        ticker = self.ib.reqMktData(contract, '', False, False)
        self.tickers[symbol] = ticker
        self.active_contracts.add(contract)
        
    def onPendingTickers(self, tickers):
        for ticker in tickers:
            self.process_ticker(ticker)
            
    def process_ticker(self, ticker):
        symbol = ticker.contract.symbol
        print(f"{symbol}: {ticker.last}")
        
        # Always yield control in callbacks
        self.ib.sleep(0)
        
    def onError(self, reqId, errorCode, errorString, contract):
        logging.error(f"Error {errorCode}: {errorString}")
        
    def shutdown(self):
        for contract in self.active_contracts:
            self.ib.cancelMktData(contract)
        self.ib.sleep(1)
        self.ib.disconnect()
        
    def run(self):
        try:
            self.ib.run()
        except KeyboardInterrupt:
            print("Shutting down...")
        finally:
            self.shutdown()

# Usage
if __name__ == '__main__':
    system = TradingSystem()
    system.connect()
    system.subscribe('AAPL')
    system.subscribe('GOOGL')
    system.run()
```

### Performance optimization summary

**Always use ib.sleep()** instead of time.sleep(). **Yield control** with ib.sleep(0) in long-running callbacks. **Set TWS memory** to 4096 MB minimum. **Use event handlers** instead of polling loops. **Limit buffer sizes** to prevent memory growth. **Remove event handlers** before unsubscribing. **Use same contract object** for cancellation. **Process data quickly** in callbacks, defer heavy computation. **Monitor subscription limits** (100 market data, 3 tick-by-tick). **Use reqTickers()** for efficient bulk snapshot requests.

---

## Conclusion: Building robust trading systems

The ib_insync library transforms Interactive Brokers' complex native API into a clean, Pythonic interface ideal for algorithmic trading applications. Success hinges on understanding three core principles: never block the event loop with time.sleep(), always access fresh state rather than caching copies, and leverage event-driven patterns for real-time data processing.

For asynchronous programming, choose the appropriate interface—blocking methods for simple scripts, async methods for high-performance concurrent operations. Manage the event loop carefully using util.patchAsyncio() in notebooks and yielding control with ib.sleep() in long operations. Subscribe to events rather than polling for maximum efficiency.

The single source of truth pattern maintains automatic synchronization between your application and TWS/Gateway. Access current state through IB methods like positions() and portfolio() rather than storing stale copies. Trust that Trade and Ticker objects update automatically in the background as state changes.

Order placement requires proper contract qualification before execution, careful transmit flag management for bracket and OCO orders, and comprehensive monitoring through both orderStatus and execDetails events. Test complex order types in paper accounts before live trading.

Futures contracts demand specific identification through localSymbol, exact expiry dates, or conId to avoid ambiguity. Implement rollover detection and front month selection for continuous trading strategies. Always qualify contracts before use and use correct exchange specifications (CME instead of GLOBEX).

Live data streaming provides multiple subscription methods—reqMktData for ticks, reqRealTimeBars for 5-second bars, keepUpToDate for streaming historical bars. Process data through event handlers for efficiency, monitor subscription limits, and always use the same contract object for cancellation as subscription.

The library's original version remains stable while the active successor ib_async continues development. Both share the same core patterns documented in this guide. Install with pip, configure TWS/Gateway with 4096 MB memory minimum, enable API access, and start building sophisticated trading systems with confidence.
