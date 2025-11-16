# ib-insync Advanced Patterns & Scenarios
**Advanced Trading Strategies | Error Handling | Complex Orders**

> **Companion to**: ib_insync_complete_reference.md  
> **Focus**: Production-ready patterns, edge cases, advanced order types  
> **Use Case**: AI-assisted complex trading system development

---

## 📋 Table of Contents

1. [Advanced Order Types](#advanced-orders)
2. [Multi-Leg Options Strategies](#options-strategies)
3. [Error Handling & Recovery](#error-handling)
4. [Position Management](#position-management)
5. [Risk Management Patterns](#risk-management)
6. [Reconnection Logic](#reconnection)
7. [Portfolio Rebalancing](#rebalancing)
8. [Advanced Market Data](#advanced-data)
9. [Multi-Account Management](#multi-account)
10. [Performance Optimization](#optimization)
11. [Production Deployment](#production)

---

## 🎯 Advanced Order Types {#advanced-orders}

### Conditional Orders

#### Price-Based Condition
```python
from ib_insync import *

ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)

# Order triggers when SPY hits 450
contract = Stock('AAPL', 'SMART', 'USD')
trigger_contract = Stock('SPY', 'SMART', 'USD')

# Qualify both
contract, trigger_contract = ib.qualifyContracts(contract, trigger_contract)

# Create price condition
condition = PriceCondition(
    condType=1,  # Price
    conId=trigger_contract.conId,
    exchange='SMART',
    isMore=True,  # True = above, False = below
    price=450.0
)

# Create order with condition
order = LimitOrder('BUY', 100, 175.0)
order.conditions = [condition]
order.conditionsIgnoreRth = False
order.conditionsCancelOrder = False

trade = ib.placeOrder(contract, order)
print(f"Conditional order placed: {trade.order.orderId}")
```

#### Time-Based Condition
```python
from datetime import datetime, timedelta

# Order triggers at specific time
time_condition = TimeCondition(
    condType=3,  # Time
    isMore=True,
    time=datetime.now() + timedelta(hours=1)
)

order = MarketOrder('BUY', 100)
order.conditions = [time_condition]
trade = ib.placeOrder(contract, order)
```

#### Volume-Based Condition
```python
# Trigger when daily volume exceeds threshold
volume_condition = VolumeCondition(
    condType=4,  # Volume
    conId=contract.conId,
    exchange='SMART',
    isMore=True,
    volume=10000000  # 10M shares
)

order = LimitOrder('BUY', 100, 175.0)
order.conditions = [volume_condition]
trade = ib.placeOrder(contract, order)
```

#### Multiple Conditions (AND/OR)
```python
# Order triggers when BOTH conditions met
price_cond = PriceCondition(
    condType=1,
    conId=trigger_contract.conId,
    exchange='SMART',
    isMore=True,
    price=450.0
)

volume_cond = VolumeCondition(
    condType=4,
    conId=contract.conId,
    exchange='SMART',
    isMore=True,
    volume=5000000
)

order = LimitOrder('BUY', 100, 175.0)
order.conditions = [price_cond, volume_cond]
order.conditionsIgnoreRth = False
order.conditionsCancelOrder = False  # False = AND, True = OR

trade = ib.placeOrder(contract, order)
```

### Trailing Stop Orders

#### Trailing Stop Loss (Percentage)
```python
order = Order()
order.action = 'SELL'
order.totalQuantity = 100
order.orderType = 'TRAIL'
order.trailingPercent = 2.0  # Trail by 2%
order.tif = 'GTC'

trade = ib.placeOrder(contract, order)
```

#### Trailing Stop Loss (Fixed Amount)
```python
order = Order()
order.action = 'SELL'
order.totalQuantity = 100
order.orderType = 'TRAIL'
order.auxPrice = 5.0  # Trail by $5
order.tif = 'GTC'

trade = ib.placeOrder(contract, order)
```

#### Trailing Stop Limit
```python
order = Order()
order.action = 'SELL'
order.totalQuantity = 100
order.orderType = 'TRAIL LIMIT'
order.lmtPriceOffset = 0.50  # Limit $0.50 below trail
order.trailingPercent = 2.0
order.tif = 'GTC'

trade = ib.placeOrder(contract, order)
```

### Pegged Orders

#### Pegged to Market (Midpoint)
```python
order = Order()
order.action = 'BUY'
order.totalQuantity = 100
order.orderType = 'PEG MID'
order.tif = 'GTC'

trade = ib.placeOrder(contract, order)
```

#### Pegged to Best Bid/Ask
```python
order = Order()
order.action = 'BUY'
order.totalQuantity = 100
order.orderType = 'PEG BEST'
order.tif = 'GTC'

trade = ib.placeOrder(contract, order)
```

#### Relative Order (Offset from NBBO)
```python
order = Order()
order.action = 'BUY'
order.totalQuantity = 100
order.orderType = 'REL'
order.lmtPrice = 0.10  # $0.10 above best bid
order.tif = 'GTC'

trade = ib.placeOrder(contract, order)
```

### One-Cancels-All (OCA) Groups

#### Multiple Exits from Same Entry
```python
# Buy at market, then set multiple exit strategies
entry_order = MarketOrder('BUY', 100)
entry_trade = ib.placeOrder(contract, entry_order)

# Wait for fill
while not entry_trade.isDone():
    ib.sleep(0.1)

if entry_trade.orderStatus.status == 'Filled':
    # Create OCA group for exits
    oca_group = f"OCA_{int(time.time())}"
    
    # Exit 1: Take profit at +5%
    exit1 = LimitOrder('SELL', 100, entry_trade.orderStatus.avgFillPrice * 1.05)
    exit1.ocaGroup = oca_group
    exit1.ocaType = 1  # Cancel all on fill
    
    # Exit 2: Stop loss at -2%
    exit2 = StopOrder('SELL', 100, entry_trade.orderStatus.avgFillPrice * 0.98)
    exit2.ocaGroup = oca_group
    exit2.ocaType = 1
    
    # Exit 3: Trailing stop
    exit3 = Order()
    exit3.action = 'SELL'
    exit3.totalQuantity = 100
    exit3.orderType = 'TRAIL'
    exit3.trailingPercent = 3.0
    exit3.ocaGroup = oca_group
    exit3.ocaType = 1
    
    for order in [exit1, exit2, exit3]:
        ib.placeOrder(contract, order)
```

### Algorithmic Orders

#### TWAP (Time-Weighted Average Price)
```python
order = Order()
order.action = 'BUY'
order.totalQuantity = 10000  # Large order
order.orderType = 'LMT'
order.lmtPrice = 175.0
order.tif = 'DAY'

# TWAP algo
order.algoStrategy = 'Twap'
order.algoParams = [
    TagValue('startTime', '09:30:00 EST'),
    TagValue('endTime', '16:00:00 EST'),
    TagValue('allowPastEndTime', '1')
]

trade = ib.placeOrder(contract, order)
```

#### VWAP (Volume-Weighted Average Price)
```python
order = Order()
order.action = 'BUY'
order.totalQuantity = 10000
order.orderType = 'LMT'
order.lmtPrice = 175.0
order.tif = 'DAY'

order.algoStrategy = 'Vwap'
order.algoParams = [
    TagValue('maxPctVol', '0.1'),  # Max 10% of volume
    TagValue('startTime', '09:30:00 EST'),
    TagValue('endTime', '16:00:00 EST'),
    TagValue('allowPastEndTime', '1'),
    TagValue('noTakeLiq', '1')
]

trade = ib.placeOrder(contract, order)
```

#### Adaptive (IB's Smart Routing)
```python
order = Order()
order.action = 'BUY'
order.totalQuantity = 1000
order.orderType = 'LMT'
order.lmtPrice = 175.0
order.tif = 'DAY'

order.algoStrategy = 'Adaptive'
order.algoParams = [
    TagValue('adaptivePriority', 'Normal')  # Urgent, Normal, Patient
]

trade = ib.placeOrder(contract, order)
```

---

## 🎲 Multi-Leg Options Strategies {#options-strategies}

### Vertical Spread (Bull Call Spread)
```python
from ib_insync import *

ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)

# Define legs
buy_call = Option('SPY', '20240315', 450, 'C', 'SMART')
sell_call = Option('SPY', '20240315', 460, 'C', 'SMART')

# Qualify
buy_call, sell_call = ib.qualifyContracts(buy_call, sell_call)

# Create combo contract
combo = Contract()
combo.symbol = 'SPY'
combo.secType = 'BAG'
combo.currency = 'USD'
combo.exchange = 'SMART'

# Define legs
leg1 = ComboLeg()
leg1.conId = buy_call.conId
leg1.ratio = 1
leg1.action = 'BUY'
leg1.exchange = 'SMART'

leg2 = ComboLeg()
leg2.conId = sell_call.conId
leg2.ratio = 1
leg2.action = 'SELL'
leg2.exchange = 'SMART'

combo.comboLegs = [leg1, leg2]

# Place order
order = LimitOrder('BUY', 10, 5.50)  # Debit spread for $5.50
trade = ib.placeOrder(combo, order)
```

### Iron Condor
```python
# Four-leg strategy: sell OTM call spread + sell OTM put spread
buy_call = Option('SPY', '20240315', 470, 'C', 'SMART')
sell_call = Option('SPY', '20240315', 465, 'C', 'SMART')
buy_put = Option('SPY', '20240315', 430, 'P', 'SMART')
sell_put = Option('SPY', '20240315', 435, 'P', 'SMART')

# Qualify all
contracts = ib.qualifyContracts(buy_call, sell_call, buy_put, sell_put)

# Create BAG
combo = Contract()
combo.symbol = 'SPY'
combo.secType = 'BAG'
combo.currency = 'USD'
combo.exchange = 'SMART'

combo.comboLegs = [
    ComboLeg(conId=contracts[0].conId, ratio=1, action='BUY', exchange='SMART'),   # Buy call
    ComboLeg(conId=contracts[1].conId, ratio=1, action='SELL', exchange='SMART'),  # Sell call
    ComboLeg(conId=contracts[2].conId, ratio=1, action='BUY', exchange='SMART'),   # Buy put
    ComboLeg(conId=contracts[3].conId, ratio=1, action='SELL', exchange='SMART'),  # Sell put
]

# Place as credit spread
order = LimitOrder('SELL', 10, 2.00)  # Collect $2.00 credit
trade = ib.placeOrder(combo, order)
```

### Butterfly Spread
```python
# Buy 1 ITM call, Sell 2 ATM calls, Buy 1 OTM call
lower_call = Option('SPY', '20240315', 440, 'C', 'SMART')
middle_call = Option('SPY', '20240315', 450, 'C', 'SMART')
upper_call = Option('SPY', '20240315', 460, 'C', 'SMART')

contracts = ib.qualifyContracts(lower_call, middle_call, upper_call)

combo = Contract()
combo.symbol = 'SPY'
combo.secType = 'BAG'
combo.currency = 'USD'
combo.exchange = 'SMART'

combo.comboLegs = [
    ComboLeg(conId=contracts[0].conId, ratio=1, action='BUY', exchange='SMART'),
    ComboLeg(conId=contracts[1].conId, ratio=2, action='SELL', exchange='SMART'),  # 2x middle
    ComboLeg(conId=contracts[2].conId, ratio=1, action='BUY', exchange='SMART'),
]

order = LimitOrder('BUY', 10, 1.50)
trade = ib.placeOrder(combo, order)
```

### Calendar Spread
```python
# Sell near-term, buy far-term (same strike)
near_call = Option('SPY', '20240315', 450, 'C', 'SMART')
far_call = Option('SPY', '20240615', 450, 'C', 'SMART')

contracts = ib.qualifyContracts(near_call, far_call)

combo = Contract()
combo.symbol = 'SPY'
combo.secType = 'BAG'
combo.currency = 'USD'
combo.exchange = 'SMART'

combo.comboLegs = [
    ComboLeg(conId=contracts[0].conId, ratio=1, action='SELL', exchange='SMART'),
    ComboLeg(conId=contracts[1].conId, ratio=1, action='BUY', exchange='SMART'),
]

order = LimitOrder('BUY', 10, 0.75)
trade = ib.placeOrder(combo, order)
```

### Delta Hedging Pattern
```python
# Dynamic delta hedging for options position
def calculate_position_delta(portfolio):
    """Calculate total portfolio delta"""
    total_delta = 0.0
    
    for item in portfolio:
        if item.contract.secType == 'OPT':
            # Request option computations
            ticker = ib.reqMktData(item.contract, '', False, False)
            ib.sleep(1)
            
            if ticker.modelGreeks:
                delta = ticker.modelGreeks.delta
                total_delta += delta * item.position
            
            ib.cancelMktData(item.contract)
    
    return total_delta

def hedge_delta(underlying_contract, target_delta=0.0):
    """Adjust underlying position to achieve target delta"""
    portfolio = ib.portfolio()
    current_delta = calculate_position_delta(portfolio)
    
    delta_to_hedge = current_delta - target_delta
    
    if abs(delta_to_hedge) > 0.1:  # Threshold
        # Delta of stock is 1.0
        shares_to_trade = int(delta_to_hedge * 100)  # Per contract
        
        if shares_to_trade > 0:
            order = MarketOrder('SELL', abs(shares_to_trade))
        else:
            order = MarketOrder('BUY', abs(shares_to_trade))
        
        trade = ib.placeOrder(underlying_contract, order)
        print(f"Hedging {shares_to_trade} shares | Current delta: {current_delta:.2f}")
        
        return trade
    else:
        print(f"Delta within tolerance: {current_delta:.2f}")
        return None

# Run periodically
underlying = Stock('SPY', 'SMART', 'USD')
underlying = ib.qualifyContracts(underlying)[0]

while True:
    hedge_delta(underlying, target_delta=0.0)
    ib.sleep(300)  # Every 5 minutes
```

---

## 🛡️ Error Handling & Recovery {#error-handling}

### Comprehensive Error Handler
```python
from ib_insync import *
import logging

class IBErrorHandler:
    def __init__(self, ib):
        self.ib = ib
        self.error_log = []
        self.ib.errorEvent += self.on_error
        
    def on_error(self, reqId, errorCode, errorString, contract):
        """Centralized error handling"""
        error_info = {
            'time': datetime.now(),
            'reqId': reqId,
            'code': errorCode,
            'message': errorString,
            'contract': contract
        }
        self.error_log.append(error_info)
        
        # Categorize and handle
        if errorCode in [502, 503, 504]:
            self.handle_connection_error(errorCode, errorString)
        elif errorCode in [200, 201, 202]:
            self.handle_order_error(errorCode, errorString, contract)
        elif errorCode == 162:
            self.handle_data_error(errorCode, errorString, contract)
        elif errorCode == 354:
            self.handle_market_data_subscription_error(errorCode, errorString)
        elif errorCode in [2104, 2106, 2158]:
            # Info messages - ignore
            pass
        else:
            logging.error(f"Error {errorCode}: {errorString}")
    
    def handle_connection_error(self, code, message):
        """Handle connection failures"""
        logging.critical(f"Connection error {code}: {message}")
        # Trigger reconnection
        self.schedule_reconnect()
    
    def handle_order_error(self, code, message, contract):
        """Handle order rejections"""
        logging.error(f"Order error {code}: {message} for {contract}")
        # Could retry with modified params
        # Or alert user
    
    def handle_data_error(self, code, message, contract):
        """Handle data request failures"""
        logging.warning(f"Data error {code}: {message} for {contract}")
        # Retry with different params
    
    def handle_market_data_subscription_error(self, code, message):
        """Handle market data subscription issues"""
        logging.warning(f"Market data error {code}: {message}")
        # Fall back to delayed data
        self.ib.reqMarketDataType(3)  # Delayed
    
    def schedule_reconnect(self):
        """Schedule reconnection attempt"""
        # Implementation in reconnection section
        pass

# Usage
ib = IB()
error_handler = IBErrorHandler(ib)
ib.connect('127.0.0.1', 7497, clientId=1)
```

### Order Validation Before Submission
```python
def validate_order(ib, contract, order):
    """Validate order before placing"""
    errors = []
    
    # 1. Check contract is qualified
    if contract.conId == 0:
        errors.append("Contract not qualified")
    
    # 2. Check buying power
    account_values = {v.tag: float(v.value) for v in ib.accountValues() if v.tag in ['BuyingPower', 'NetLiquidation']}
    
    if order.action == 'BUY':
        # Estimate cost
        ticker = ib.reqMktData(contract, '', True, False)  # Snapshot
        ib.sleep(1)
        
        if ticker.ask and ticker.ask == ticker.ask:  # Not NaN
            estimated_cost = ticker.ask * order.totalQuantity
            if estimated_cost > account_values.get('BuyingPower', 0):
                errors.append(f"Insufficient buying power: need ${estimated_cost:.2f}, have ${account_values.get('BuyingPower', 0):.2f}")
        
        ib.cancelMktData(contract)
    
    # 3. What-if order check
    try:
        order_copy = Order(**{k: v for k, v in order.__dict__.items()})
        order_copy.whatIf = True
        
        orderState = ib.whatIfOrder(contract, order_copy)
        
        if orderState.commission and orderState.commission > 0:
            # Valid response
            if float(orderState.initMarginAfter) > account_values.get('NetLiquidation', 0):
                errors.append("Insufficient margin")
        else:
            errors.append("What-if order returned invalid state")
            
    except Exception as e:
        errors.append(f"What-if validation failed: {e}")
    
    # 4. Check trading hours
    details = ib.reqContractDetails(contract)
    if details:
        # Parse trading hours (simplified)
        # Would need full implementation
        pass
    
    return errors

# Usage
contract = Stock('AAPL', 'SMART', 'USD')
contract = ib.qualifyContracts(contract)[0]
order = LimitOrder('BUY', 1000, 175.0)

validation_errors = validate_order(ib, contract, order)
if validation_errors:
    print("Order validation failed:")
    for error in validation_errors:
        print(f"  - {error}")
else:
    trade = ib.placeOrder(contract, order)
    print("Order placed successfully")
```

### Retry Logic with Exponential Backoff
```python
import time
from functools import wraps

def retry_with_backoff(max_retries=3, base_delay=1.0, max_delay=60.0):
    """Decorator for retrying failed operations"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            delay = base_delay
            
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries >= max_retries:
                        logging.error(f"{func.__name__} failed after {max_retries} retries: {e}")
                        raise
                    
                    logging.warning(f"{func.__name__} failed (attempt {retries}/{max_retries}): {e}. Retrying in {delay}s...")
                    time.sleep(delay)
                    delay = min(delay * 2, max_delay)  # Exponential backoff
            
        return wrapper
    return decorator

# Usage
@retry_with_backoff(max_retries=3, base_delay=2.0)
def place_order_with_retry(ib, contract, order):
    """Place order with automatic retry"""
    trade = ib.placeOrder(contract, order)
    
    # Wait for submission
    timeout = 10
    start = time.time()
    while trade.orderStatus.status in ['PendingSubmit', '']:
        if time.time() - start > timeout:
            raise TimeoutError("Order submission timeout")
        ib.sleep(0.1)
    
    if trade.orderStatus.status in ['Cancelled', 'ApiCancelled']:
        raise Exception(f"Order cancelled: {trade.orderStatus.status}")
    
    return trade

# Usage
try:
    trade = place_order_with_retry(ib, contract, order)
    print(f"Order placed: {trade.order.orderId}")
except Exception as e:
    print(f"Order failed: {e}")
```

---

## 📊 Position Management {#position-management}

### Position Reconciliation
```python
class PositionManager:
    def __init__(self, ib):
        self.ib = ib
        self.expected_positions = {}  # conId -> quantity
        
    def record_trade(self, trade):
        """Record expected position change"""
        if trade.orderStatus.status == 'Filled':
            conId = trade.contract.conId
            qty = trade.filled() if trade.order.action == 'BUY' else -trade.filled()
            
            if conId in self.expected_positions:
                self.expected_positions[conId] += qty
            else:
                self.expected_positions[conId] = qty
    
    def reconcile(self):
        """Check actual vs expected positions"""
        actual_positions = {p.contract.conId: p.position for p in self.ib.positions()}
        
        discrepancies = []
        
        # Check expected positions
        for conId, expected_qty in self.expected_positions.items():
            actual_qty = actual_positions.get(conId, 0)
            if abs(actual_qty - expected_qty) > 0.01:  # Allow for rounding
                discrepancies.append({
                    'conId': conId,
                    'expected': expected_qty,
                    'actual': actual_qty,
                    'diff': actual_qty - expected_qty
                })
        
        # Check for unexpected positions
        for conId, actual_qty in actual_positions.items():
            if conId not in self.expected_positions and abs(actual_qty) > 0.01:
                discrepancies.append({
                    'conId': conId,
                    'expected': 0,
                    'actual': actual_qty,
                    'diff': actual_qty
                })
        
        if discrepancies:
            logging.warning(f"Position discrepancies found: {discrepancies}")
        
        return discrepancies
    
    def reset_tracking(self):
        """Reset to current positions"""
        self.expected_positions = {
            p.contract.conId: p.position 
            for p in self.ib.positions()
        }

# Usage
pm = PositionManager(ib)
pm.reset_tracking()

# Track trades
ib.execDetailsEvent += lambda trade, fill: pm.record_trade(trade)

# Periodic reconciliation
while True:
    discrepancies = pm.reconcile()
    if discrepancies:
        # Alert or take action
        pass
    ib.sleep(60)
```

### Close All Positions
```python
def close_all_positions(ib, exclude_symbols=None):
    """Emergency position closer"""
    exclude_symbols = exclude_symbols or []
    
    positions = ib.positions()
    trades = []
    
    for position in positions:
        symbol = position.contract.symbol
        
        if symbol in exclude_symbols:
            continue
        
        qty = abs(position.position)
        action = 'SELL' if position.position > 0 else 'BUY'
        
        order = MarketOrder(action, qty)
        trade = ib.placeOrder(position.contract, order)
        trades.append(trade)
        
        print(f"Closing {action} {qty} {symbol}")
    
    # Wait for all to fill
    timeout = 30
    start = time.time()
    
    while any(not t.isDone() for t in trades):
        if time.time() - start > timeout:
            logging.error("Timeout waiting for position closures")
            break
        ib.sleep(0.5)
    
    return trades

# Usage - emergency exit
if emergency_condition:
    close_all_positions(ib)
```

### Position Size Calculator
```python
def calculate_position_size(
    ib,
    contract,
    risk_per_trade_pct=0.02,  # 2% risk
    stop_loss_pct=0.05         # 5% stop
):
    """Calculate position size based on risk"""
    
    # Get account value
    account_values = {v.tag: float(v.value) for v in ib.accountValues()}
    net_liq = account_values.get('NetLiquidation', 0)
    
    # Calculate dollar risk
    dollar_risk = net_liq * risk_per_trade_pct
    
    # Get current price
    ticker = ib.reqMktData(contract, '', True, False)
    ib.sleep(1)
    
    if not ticker.last or ticker.last != ticker.last:  # NaN check
        logging.error("Unable to get price for position sizing")
        return 0
    
    price = ticker.last
    ib.cancelMktData(contract)
    
    # Calculate shares
    # dollar_risk = shares * price * stop_loss_pct
    shares = dollar_risk / (price * stop_loss_pct)
    
    # Round to nearest tradeable lot
    if contract.secType == 'OPT':
        shares = int(shares / 100) * 100  # Options in contracts (100 shares)
    else:
        shares = int(shares)
    
    print(f"Position size for {contract.symbol}: {shares} shares")
    print(f"At ${price:.2f}, risking ${dollar_risk:.2f} ({risk_per_trade_pct*100}% of ${net_liq:.2f})")
    
    return shares

# Usage
contract = Stock('AAPL', 'SMART', 'USD')
contract = ib.qualifyContracts(contract)[0]

shares = calculate_position_size(ib, contract, risk_per_trade_pct=0.01, stop_loss_pct=0.03)

if shares > 0:
    order = LimitOrder('BUY', shares, 175.0)
    trade = ib.placeOrder(contract, order)
```

---

## ⚠️ Risk Management Patterns {#risk-management}

### Daily Loss Limit
```python
class DailyLossLimiter:
    def __init__(self, ib, max_daily_loss_pct=0.05):
        self.ib = ib
        self.max_daily_loss_pct = max_daily_loss_pct
        self.start_equity = None
        self.breached = False
        
    def initialize(self):
        """Set starting equity for the day"""
        account_values = {v.tag: float(v.value) for v in self.ib.accountValues()}
        self.start_equity = account_values.get('NetLiquidation', 0)
        self.breached = False
        print(f"Daily loss limiter initialized. Start equity: ${self.start_equity:.2f}")
    
    def check_limit(self):
        """Check if daily loss limit breached"""
        if self.breached:
            return True
        
        account_values = {v.tag: float(v.value) for v in self.ib.accountValues()}
        current_equity = account_values.get('NetLiquidation', 0)
        
        loss = self.start_equity - current_equity
        loss_pct = loss / self.start_equity if self.start_equity > 0 else 0
        
        if loss_pct >= self.max_daily_loss_pct:
            self.breached = True
            logging.critical(f"DAILY LOSS LIMIT BREACHED! Loss: ${loss:.2f} ({loss_pct*100:.2f}%)")
            return True
        
        return False
    
    def enforce(self):
        """Close all positions and cancel all orders"""
        if not self.breached:
            return
        
        print("Enforcing daily loss limit...")
        
        # Cancel all orders
        self.ib.reqGlobalCancel()
        
        # Close all positions
        close_all_positions(self.ib)
        
        print("All positions closed. Trading halted for the day.")

# Usage
limiter = DailyLossLimiter(ib, max_daily_loss_pct=0.03)  # 3% daily loss limit
limiter.initialize()

# Check periodically
while True:
    if limiter.check_limit():
        limiter.enforce()
        break
    ib.sleep(60)
```

### Max Position Concentration
```python
def check_position_concentration(ib, max_position_pct=0.20):
    """Ensure no single position exceeds % of portfolio"""
    
    account_values = {v.tag: float(v.value) for v in ib.accountValues()}
    net_liq = account_values.get('NetLiquidation', 0)
    
    violations = []
    
    for item in ib.portfolio():
        position_pct = abs(item.marketValue) / net_liq if net_liq > 0 else 0
        
        if position_pct > max_position_pct:
            violations.append({
                'symbol': item.contract.symbol,
                'value': item.marketValue,
                'pct': position_pct,
                'limit': max_position_pct
            })
    
    if violations:
        logging.warning(f"Position concentration violations: {violations}")
    
    return violations

# Check before placing order
def place_order_with_concentration_check(ib, contract, order, max_pct=0.20):
    """Place order only if it doesn't violate concentration"""
    
    # Estimate new position value
    ticker = ib.reqMktData(contract, '', True, False)
    ib.sleep(1)
    
    if ticker.ask:
        estimated_value = ticker.ask * order.totalQuantity
        
        account_values = {v.tag: float(v.value) for v in ib.accountValues()}
        net_liq = account_values.get('NetLiquidation', 0)
        
        # Get current position
        current_position = next(
            (p.marketValue for p in ib.portfolio() if p.contract.conId == contract.conId),
            0
        )
        
        new_position_value = abs(current_position + estimated_value)
        new_pct = new_position_value / net_liq if net_liq > 0 else 0
        
        if new_pct > max_pct:
            logging.error(f"Order would violate concentration limit: {new_pct*100:.1f}% > {max_pct*100:.1f}%")
            ib.cancelMktData(contract)
            return None
    
    ib.cancelMktData(contract)
    return ib.placeOrder(contract, order)
```

### Correlation-Based Risk
```python
import numpy as np
import pandas as pd

def calculate_portfolio_correlation_risk(ib, lookback_days=30):
    """Calculate portfolio correlation matrix"""
    
    portfolio = ib.portfolio()
    symbols = [p.contract.symbol for p in portfolio if p.contract.secType == 'STK']
    
    # Get historical data for all positions
    price_data = {}
    
    for symbol in symbols:
        contract = Stock(symbol, 'SMART', 'USD')
        contract = ib.qualifyContracts(contract)[0]
        
        bars = ib.reqHistoricalData(
            contract,
            endDateTime='',
            durationStr=f'{lookback_days} D',
            barSizeSetting='1 day',
            whatToShow='TRADES',
            useRTH=True
        )
        
        if bars:
            price_data[symbol] = [bar.close for bar in bars]
    
    # Create DataFrame
    df = pd.DataFrame(price_data)
    
    # Calculate returns
    returns = df.pct_change().dropna()
    
    # Correlation matrix
    corr_matrix = returns.corr()
    
    # Identify highly correlated pairs
    high_corr_threshold = 0.7
    high_corr_pairs = []
    
    for i in range(len(corr_matrix.columns)):
        for j in range(i+1, len(corr_matrix.columns)):
            corr = corr_matrix.iloc[i, j]
            if abs(corr) > high_corr_threshold:
                high_corr_pairs.append({
                    'symbol1': corr_matrix.columns[i],
                    'symbol2': corr_matrix.columns[j],
                    'correlation': corr
                })
    
    if high_corr_pairs:
        logging.warning(f"High correlation detected: {high_corr_pairs}")
    
    return corr_matrix, high_corr_pairs

# Usage
corr_matrix, high_corr = calculate_portfolio_correlation_risk(ib)
print("Portfolio Correlation Matrix:")
print(corr_matrix)
```

---

## 🔄 Reconnection Logic {#reconnection}

### Auto-Reconnect Manager
```python
class ReconnectionManager:
    def __init__(self, host='127.0.0.1', port=7497, clientId=1):
        self.host = host
        self.port = port
        self.clientId = clientId
        self.ib = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        self.reconnect_delay = 5
        self.is_connected = False
        
    def connect(self):
        """Initial connection with reconnect logic"""
        while self.reconnect_attempts < self.max_reconnect_attempts:
            try:
                self.ib = IB()
                self.ib.disconnectedEvent += self.on_disconnect
                self.ib.errorEvent += self.on_error
                
                self.ib.connect(
                    self.host,
                    self.port,
                    self.clientId,
                    timeout=10
                )
                
                self.is_connected = True
                self.reconnect_attempts = 0
                logging.info(f"Connected to TWS at {self.host}:{self.port}")
                
                # Restore subscriptions
                self.restore_state()
                
                return self.ib
                
            except Exception as e:
                self.reconnect_attempts += 1
                logging.error(f"Connection attempt {self.reconnect_attempts} failed: {e}")
                
                if self.reconnect_attempts >= self.max_reconnect_attempts:
                    logging.critical("Max reconnection attempts reached. Giving up.")
                    raise
                
                logging.info(f"Retrying in {self.reconnect_delay} seconds...")
                time.sleep(self.reconnect_delay)
                self.reconnect_delay = min(self.reconnect_delay * 2, 60)  # Exponential backoff
    
    def on_disconnect(self):
        """Handle disconnection"""
        self.is_connected = False
        logging.warning("Disconnected from TWS. Attempting reconnect...")
        
        # Save current state
        self.save_state()
        
        # Attempt reconnection
        self.connect()
    
    def on_error(self, reqId, errorCode, errorString, contract):
        """Handle connection errors"""
        if errorCode in [502, 503, 504, 1100, 1101, 1102]:
            logging.error(f"Connection error {errorCode}: {errorString}")
            if not self.is_connected:
                self.on_disconnect()
    
    def save_state(self):
        """Save subscriptions and state before disconnect"""
        if not self.ib:
            return
        
        # Save tickers
        self.saved_tickers = [
            (ticker.contract, ticker.genericTickList) 
            for ticker in self.ib.tickers()
        ]
        
        # Save positions (for monitoring)
        self.saved_positions = [
            (p.contract, p.position) 
            for p in self.ib.positions()
        ]
        
        logging.info(f"Saved state: {len(self.saved_tickers)} tickers, {len(self.saved_positions)} positions")
    
    def restore_state(self):
        """Restore subscriptions after reconnect"""
        if not hasattr(self, 'saved_tickers'):
            return
        
        logging.info("Restoring market data subscriptions...")
        
        # Resubscribe to tickers
        for contract, genericTickList in self.saved_tickers:
            try:
                self.ib.reqMktData(contract, genericTickList, False, False)
            except Exception as e:
                logging.error(f"Failed to restore ticker {contract.symbol}: {e}")
        
        logging.info("State restored")

# Usage
conn_mgr = ReconnectionManager(host='127.0.0.1', port=7497, clientId=1)
ib = conn_mgr.connect()

# Normal trading operations
# Connection will auto-reconnect on failure
```

### Heartbeat Monitor
```python
class HeartbeatMonitor:
    def __init__(self, ib, timeout=60):
        self.ib = ib
        self.timeout = timeout
        self.last_update = time.time()
        self.ib.updateEvent += self.on_update
        
    def on_update(self):
        """Reset timer on any update"""
        self.last_update = time.time()
    
    def check(self):
        """Check if connection is alive"""
        elapsed = time.time() - self.last_update
        
        if elapsed > self.timeout:
            logging.warning(f"No updates for {elapsed:.0f}s. Connection may be dead.")
            return False
        
        return True
    
    def run(self):
        """Run heartbeat check loop"""
        while True:
            if not self.check():
                logging.error("Heartbeat timeout. Triggering reconnect...")
                # Trigger reconnection
                break
            
            time.sleep(10)

# Usage
heartbeat = HeartbeatMonitor(ib, timeout=60)
# Run in separate thread or async task
```

---

## 📐 Portfolio Rebalancing {#rebalancing}

### Target Allocation Rebalancer
```python
class PortfolioRebalancer:
    def __init__(self, ib):
        self.ib = ib
        
    def rebalance_to_target(self, target_allocations, tolerance=0.05):
        """
        Rebalance portfolio to target allocations
        
        Args:
            target_allocations: Dict[symbol: str, target_pct: float]
                                Example: {'AAPL': 0.25, 'GOOGL': 0.25, 'MSFT': 0.50}
            tolerance: Rebalance threshold (0.05 = 5%)
        """
        
        # Validate target allocations
        total = sum(target_allocations.values())
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Target allocations must sum to 1.0, got {total}")
        
        # Get current portfolio
        account_values = {v.tag: float(v.value) for v in self.ib.accountValues()}
        net_liq = account_values.get('NetLiquidation', 0)
        
        portfolio = {item.contract.symbol: item for item in self.ib.portfolio()}
        
        # Calculate current allocations
        current_allocations = {
            symbol: (item.marketValue / net_liq if net_liq > 0 else 0)
            for symbol, item in portfolio.items()
        }
        
        # Determine needed trades
        trades_needed = []
        
        for symbol, target_pct in target_allocations.items():
            current_pct = current_allocations.get(symbol, 0)
            diff = target_pct - current_pct
            
            if abs(diff) > tolerance:
                target_value = net_liq * target_pct
                current_value = portfolio[symbol].marketValue if symbol in portfolio else 0
                value_change = target_value - current_value
                
                # Get current price
                contract = Stock(symbol, 'SMART', 'USD')
                contract = self.ib.qualifyContracts(contract)[0]
                
                ticker = self.ib.reqMktData(contract, '', True, False)
                self.ib.sleep(1)
                
                if ticker.last and ticker.last == ticker.last:
                    price = ticker.last
                    shares_change = int(value_change / price)
                    
                    if shares_change != 0:
                        trades_needed.append({
                            'symbol': symbol,
                            'contract': contract,
                            'current_pct': current_pct,
                            'target_pct': target_pct,
                            'shares': shares_change,
                            'action': 'BUY' if shares_change > 0 else 'SELL'
                        })
                
                self.ib.cancelMktData(contract)
        
        # Execute trades
        if not trades_needed:
            logging.info("Portfolio within tolerance. No rebalancing needed.")
            return []
        
        logging.info(f"Rebalancing {len(trades_needed)} positions...")
        placed_trades = []
        
        for trade_info in trades_needed:
            logging.info(f"{trade_info['action']} {abs(trade_info['shares'])} {trade_info['symbol']} "
                        f"({trade_info['current_pct']*100:.1f}% -> {trade_info['target_pct']*100:.1f}%)")
            
            order = MarketOrder(trade_info['action'], abs(trade_info['shares']))
            trade = self.ib.placeOrder(trade_info['contract'], order)
            placed_trades.append(trade)
        
        return placed_trades

# Usage
target = {
    'AAPL': 0.30,
    'GOOGL': 0.30,
    'MSFT': 0.40
}

rebalancer = PortfolioRebalancer(ib)
trades = rebalancer.rebalance_to_target(target, tolerance=0.03)

# Monitor fills
for trade in trades:
    while not trade.isDone():
        ib.sleep(1)
    print(f"{trade.contract.symbol}: {trade.orderStatus.status}")
```

### Dollar-Cost Averaging
```python
class DCAScheduler:
    def __init__(self, ib):
        self.ib = ib
        self.schedules = []
        
    def add_schedule(self, symbol, amount_per_period, frequency_days):
        """
        Add DCA schedule
        
        Args:
            symbol: Stock symbol
            amount_per_period: Dollar amount to invest
            frequency_days: Days between purchases
        """
        self.schedules.append({
            'symbol': symbol,
            'amount': amount_per_period,
            'frequency': frequency_days,
            'last_purchase': None
        })
    
    def check_and_execute(self):
        """Check if any DCA purchases are due"""
        from datetime import datetime, timedelta
        
        now = datetime.now()
        
        for schedule in self.schedules:
            last = schedule['last_purchase']
            
            # Check if purchase is due
            if last is None or (now - last).days >= schedule['frequency']:
                self.execute_dca(schedule)
                schedule['last_purchase'] = now
    
    def execute_dca(self, schedule):
        """Execute DCA purchase"""
        symbol = schedule['symbol']
        amount = schedule['amount']
        
        # Create contract
        contract = Stock(symbol, 'SMART', 'USD')
        contract = self.ib.qualifyContracts(contract)[0]
        
        # Get current price
        ticker = self.ib.reqMktData(contract, '', True, False)
        self.ib.sleep(1)
        
        if ticker.last and ticker.last == ticker.last:
            price = ticker.last
            shares = int(amount / price)
            
            if shares > 0:
                logging.info(f"DCA: Buying {shares} {symbol} @ ${price:.2f} (${amount:.2f})")
                order = MarketOrder('BUY', shares)
                trade = self.ib.placeOrder(contract, order)
                return trade
        
        self.ib.cancelMktData(contract)
        return None

# Usage
dca = DCAScheduler(ib)
dca.add_schedule('SPY', 1000, 7)   # $1000 every 7 days
dca.add_schedule('VTI', 500, 14)   # $500 every 14 days

# Run daily check
while True:
    dca.check_and_execute()
    ib.sleep(86400)  # Check daily
```

---

## 📡 Advanced Market Data {#advanced-data}

### Tick-by-Tick with Filtering
```python
class TickFilter:
    def __init__(self, ib, contract, min_size=100):
        self.ib = ib
        self.contract = contract
        self.min_size = min_size
        self.large_trades = []
        
    def start(self):
        """Start tick-by-tick subscription with filtering"""
        self.ticker = self.ib.reqTickByTickData(
            self.contract,
            'AllLast',  # All trades
            0,
            False
        )
        self.ticker.updateEvent += self.on_tick
    
    def on_tick(self, ticker):
        """Filter and process ticks"""
        if not ticker.tickByTicks:
            return
        
        latest_tick = ticker.tickByTicks[-1]
        
        # Filter by size
        if latest_tick.size >= self.min_size:
            self.large_trades.append({
                'time': latest_tick.time,
                'price': latest_tick.price,
                'size': latest_tick.size
            })
            
            logging.info(f"Large trade: {latest_tick.size} @ ${latest_tick.price:.2f}")
    
    def stop(self):
        """Stop subscription"""
        self.ib.cancelTickByTickData(self.contract)
    
    def get_stats(self):
        """Get statistics on large trades"""
        if not self.large_trades:
            return None
        
        total_volume = sum(t['size'] for t in self.large_trades)
        avg_price = sum(t['price'] * t['size'] for t in self.large_trades) / total_volume
        
        return {
            'num_trades': len(self.large_trades),
            'total_volume': total_volume,
            'vwap': avg_price
        }

# Usage
contract = Stock('AAPL', 'SMART', 'USD')
contract = ib.qualifyContracts(contract)[0]

filter = TickFilter(ib, contract, min_size=1000)
filter.start()

# Run for period
ib.sleep(3600)  # 1 hour

filter.stop()
stats = filter.get_stats()
print(f"Large trades: {stats}")
```

### Volume Profile Builder
```python
class VolumeProfile:
    def __init__(self, ib, contract, num_bins=20):
        self.ib = ib
        self.contract = contract
        self.num_bins = num_bins
        self.profile = {}
        
    def build_from_historical(self, days=1):
        """Build volume profile from historical data"""
        bars = self.ib.reqHistoricalData(
            self.contract,
            endDateTime='',
            durationStr=f'{days} D',
            barSizeSetting='5 mins',
            whatToShow='TRADES',
            useRTH=True
        )
        
        if not bars:
            return None
        
        # Get price range
        prices = [bar.close for bar in bars]
        min_price = min(prices)
        max_price = max(prices)
        
        # Create bins
        bin_size = (max_price - min_price) / self.num_bins
        
        # Accumulate volume in bins
        for bar in bars:
            bin_idx = int((bar.close - min_price) / bin_size)
            bin_idx = min(bin_idx, self.num_bins - 1)  # Cap at max
            
            bin_price = min_price + (bin_idx * bin_size)
            
            if bin_price not in self.profile:
                self.profile[bin_price] = 0
            
            self.profile[bin_price] += bar.volume
        
        return self.profile
    
    def get_poc(self):
        """Get Point of Control (price with highest volume)"""
        if not self.profile:
            return None
        
        return max(self.profile.items(), key=lambda x: x[1])
    
    def get_value_area(self, percent=0.70):
        """Get value area (prices containing X% of volume)"""
        if not self.profile:
            return None
        
        total_volume = sum(self.profile.values())
        target_volume = total_volume * percent
        
        # Sort by volume
        sorted_profile = sorted(self.profile.items(), key=lambda x: x[1], reverse=True)
        
        accumulated_volume = 0
        value_area_prices = []
        
        for price, volume in sorted_profile:
            accumulated_volume += volume
            value_area_prices.append(price)
            
            if accumulated_volume >= target_volume:
                break
        
        return min(value_area_prices), max(value_area_prices)

# Usage
contract = Stock('SPY', 'SMART', 'USD')
contract = ib.qualifyContracts(contract)[0]

vp = VolumeProfile(ib, contract, num_bins=30)
profile = vp.build_from_historical(days=5)

poc_price, poc_volume = vp.get_poc()
print(f"Point of Control: ${poc_price:.2f} with {poc_volume:,.0f} volume")

va_low, va_high = vp.get_value_area(percent=0.70)
print(f"Value Area: ${va_low:.2f} - ${va_high:.2f}")
```

---

## 🏢 Multi-Account Management {#multi-account}

### Multi-Account Order Router
```python
class MultiAccountRouter:
    def __init__(self, host='127.0.0.1', port=7497):
        self.connections = {}
        self.host = host
        self.port = port
        
    def add_account(self, account_name, client_id):
        """Add account connection"""
        ib = IB()
        ib.connect(self.host, self.port, client_id)
        self.connections[account_name] = ib
        logging.info(f"Connected account {account_name} with clientId {client_id}")
    
    def place_order_all(self, contract, order_template, quantities):
        """
        Place orders across multiple accounts
        
        Args:
            contract: Contract to trade
            order_template: Base order
            quantities: Dict[account_name, quantity]
        """
        trades = {}
        
        for account_name, quantity in quantities.items():
            if account_name not in self.connections:
                logging.error(f"Account {account_name} not connected")
                continue
            
            ib = self.connections[account_name]
            
            # Clone order
            order = Order(**{k: v for k, v in order_template.__dict__.items()})
            order.totalQuantity = quantity
            order.account = account_name
            
            # Place order
            trade = ib.placeOrder(contract, order)
            trades[account_name] = trade
            
            logging.info(f"Placed {order.action} {quantity} {contract.symbol} for {account_name}")
        
        return trades
    
    def get_combined_portfolio(self):
        """Get combined portfolio across all accounts"""
        combined = {}
        
        for account_name, ib in self.connections.items():
            for item in ib.portfolio():
                symbol = item.contract.symbol
                
                if symbol not in combined:
                    combined[symbol] = {
                        'position': 0,
                        'market_value': 0,
                        'unrealized_pnl': 0,
                        'accounts': {}
                    }
                
                combined[symbol]['position'] += item.position
                combined[symbol]['market_value'] += item.marketValue
                combined[symbol]['unrealized_pnl'] += item.unrealizedPNL
                combined[symbol]['accounts'][account_name] = item.position
        
        return combined
    
    def disconnect_all(self):
        """Disconnect all accounts"""
        for account_name, ib in self.connections.items():
            ib.disconnect()
            logging.info(f"Disconnected {account_name}")

# Usage
router = MultiAccountRouter()
router.add_account('Account1', client_id=1)
router.add_account('Account2', client_id=2)
router.add_account('Account3', client_id=3)

# Place order across all accounts
contract = Stock('AAPL', 'SMART', 'USD')
order_template = LimitOrder('BUY', 0, 175.0)  # Quantity set per account

quantities = {
    'Account1': 100,
    'Account2': 200,
    'Account3': 150
}

trades = router.place_order_all(contract, order_template, quantities)

# Monitor combined portfolio
combined = router.get_combined_portfolio()
for symbol, data in combined.items():
    print(f"{symbol}: {data['position']} shares across {len(data['accounts'])} accounts")
```

---

## ⚡ Performance Optimization {#optimization}

### Batch Contract Qualification
```python
def qualify_contracts_batch(ib, contracts, batch_size=50):
    """Qualify contracts in batches to avoid rate limits"""
    qualified = []
    
    for i in range(0, len(contracts), batch_size):
        batch = contracts[i:i+batch_size]
        
        try:
            qualified_batch = ib.qualifyContracts(*batch)
            qualified.extend(qualified_batch)
        except Exception as e:
            logging.error(f"Batch qualification failed: {e}")
        
        # Respect rate limits
        ib.sleep(1)
    
    return qualified
```

### Request Queue Manager
```python
from collections import deque
import threading

class RequestQueue:
    def __init__(self, ib, max_per_second=40):
        self.ib = ib
        self.queue = deque()
        self.max_per_second = max_per_second
        self.running = False
        
    def add(self, func, *args, **kwargs):
        """Add request to queue"""
        self.queue.append((func, args, kwargs))
    
    def start(self):
        """Start processing queue"""
        self.running = True
        thread = threading.Thread(target=self._process)
        thread.daemon = True
        thread.start()
    
    def _process(self):
        """Process queue with rate limiting"""
        delay = 1.0 / self.max_per_second
        
        while self.running:
            if self.queue:
                func, args, kwargs = self.queue.popleft()
                
                try:
                    func(*args, **kwargs)
                except Exception as e:
                    logging.error(f"Request failed: {e}")
                
                time.sleep(delay)
            else:
                time.sleep(0.1)
    
    def stop(self):
        """Stop processing"""
        self.running = False

# Usage
queue = RequestQueue(ib, max_per_second=40)
queue.start()

# Queue many requests
for contract in large_contract_list:
    queue.add(ib.reqMktData, contract, '', False, False)
```

---

## 🚀 Production Deployment {#production}

### Complete Production Trading System Template
```python
"""
Production Trading System Template
Features: Auto-reconnect, error handling, risk management, logging
"""

import logging
from datetime import datetime, time as dt_time
from ib_insync import *

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(f'trading_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)

class ProductionTradingSystem:
    def __init__(self, host='127.0.0.1', port=7497, client_id=1):
        self.host = host
        self.port = port
        self.client_id = client_id
        self.ib = None
        self.running = False
        
        # Risk parameters
        self.max_daily_loss_pct = 0.03
        self.max_position_pct = 0.20
        self.daily_loss_breached = False
        
        # State tracking
        self.start_equity = 0
        self.trades_today = []
        
    def initialize(self):
        """Initialize system"""
        logging.info("Initializing trading system...")
        
        # Connect
        self.ib = IB()
        self.ib.errorEvent += self.on_error
        self.ib.disconnectedEvent += self.on_disconnect
        
        try:
            self.ib.connect(self.host, self.port, self.client_id, timeout=10)
            logging.info("Connected to TWS")
        except Exception as e:
            logging.critical(f"Failed to connect: {e}")
            return False
        
        # Get starting equity
        account_values = {v.tag: float(v.value) for v in self.ib.accountValues()}
        self.start_equity = account_values.get('NetLiquidation', 0)
        logging.info(f"Starting equity: ${self.start_equity:,.2f}")
        
        # Setup event handlers
        self.ib.orderStatusEvent += self.on_order_status
        self.ib.execDetailsEvent += self.on_execution
        
        return True
    
    def on_error(self, reqId, errorCode, errorString, contract):
        """Handle errors"""
        if errorCode in [502, 503, 504]:
            logging.error(f"Connection error {errorCode}: {errorString}")
        elif errorCode >= 2000:
            # Warnings
            logging.warning(f"Warning {errorCode}: {errorString}")
        else:
            logging.error(f"Error {errorCode}: {errorString}")
    
    def on_disconnect(self):
        """Handle disconnection"""
        logging.warning("Disconnected from TWS")
        # Attempt reconnection logic here
    
    def on_order_status(self, trade):
        """Track order status"""
        logging.info(f"Order {trade.order.orderId}: {trade.orderStatus.status}")
    
    def on_execution(self, trade, fill):
        """Track executions"""
        self.trades_today.append(trade)
        logging.info(f"Fill: {fill.execution.shares} @ ${fill.execution.price:.2f}")
    
    def check_risk_limits(self):
        """Check if risk limits breached"""
        account_values = {v.tag: float(v.value) for v in self.ib.accountValues()}
        current_equity = account_values.get('NetLiquidation', 0)
        
        # Daily loss check
        loss = self.start_equity - current_equity
        loss_pct = loss / self.start_equity if self.start_equity > 0 else 0
        
        if loss_pct >= self.max_daily_loss_pct:
            logging.critical(f"DAILY LOSS LIMIT BREACHED: {loss_pct*100:.2f}%")
            self.daily_loss_breached = True
            self.emergency_shutdown()
            return False
        
        return True
    
    def emergency_shutdown(self):
        """Emergency shutdown - close all positions"""
        logging.critical("EMERGENCY SHUTDOWN INITIATED")
        
        # Cancel all orders
        self.ib.reqGlobalCancel()
        
        # Close all positions
        for position in self.ib.positions():
            qty = abs(position.position)
            action = 'SELL' if position.position > 0 else 'BUY'
            
            order = MarketOrder(action, qty)
            self.ib.placeOrder(position.contract, order)
            
            logging.info(f"Emergency close: {action} {qty} {position.contract.symbol}")
        
        self.running = False
    
    def is_market_hours(self):
        """Check if within trading hours"""
        now = datetime.now().time()
        market_open = dt_time(9, 30)
        market_close = dt_time(16, 0)
        
        return market_open <= now <= market_close
    
    def run(self):
        """Main trading loop"""
        if not self.initialize():
            return
        
        self.running = True
        logging.info("Trading system started")
        
        try:
            while self.running:
                # Check risk limits
                if not self.check_risk_limits():
                    break
                
                # Only trade during market hours
                if self.is_market_hours():
                    # Your trading logic here
                    self.trading_logic()
                
                # Sleep between iterations
                self.ib.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            logging.info("Shutdown requested by user")
        except Exception as e:
            logging.critical(f"Unexpected error: {e}")
        finally:
            self.shutdown()
    
    def trading_logic(self):
        """Implement your trading strategy here"""
        pass
    
    def shutdown(self):
        """Graceful shutdown"""
        logging.info("Shutting down trading system...")
        
        if self.ib:
            # Cancel all market data
            for contract in [t.contract for t in self.ib.tickers()]:
                self.ib.cancelMktData(contract)
            
            # Disconnect
            self.ib.disconnect()
        
        logging.info("Shutdown complete")

# Run the system
if __name__ == '__main__':
    system = ProductionTradingSystem(
        host='127.0.0.1',
        port=7497,
        client_id=1
    )
    system.run()
```

---

## 📚 Summary

This advanced reference covers:

✅ **Conditional & Algo Orders** - Price/time/volume triggers, TWAP, VWAP  
✅ **Complex Options** - Spreads, Iron Condors, Butterflies, Delta hedging  
✅ **Error Handling** - Validation, retry logic, comprehensive error management  
✅ **Position Management** - Reconciliation, sizing, closing  
✅ **Risk Management** - Loss limits, concentration, correlation  
✅ **Reconnection Logic** - Auto-reconnect, state preservation  
✅ **Rebalancing** - Target allocation, DCA strategies  
✅ **Advanced Data** - Tick filtering, volume profiles  
✅ **Multi-Account** - Cross-account routing and management  
✅ **Optimization** - Batching, queuing, rate limiting  
✅ **Production** - Complete deployable system template

**Use with**: `ib_insync_complete_reference.md` for comprehensive API coverage

---

**End of Advanced Patterns Document**
*Optimized for AI-Assisted Development*