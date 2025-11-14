# ib-insync Orders Reference
**Quick Reference for Order Placement & Management**

## Order Types Quick Reference

### Market Order
```python
from ib_insync import *
order = MarketOrder('BUY', 100)
```

### Limit Order
```python
order = LimitOrder('BUY', 100, 175.50)
```

### Stop Order
```python
order = StopOrder('SELL', 100, 170.00)  # Stop loss
```

### Bracket Order (Entry + Exits)
```python
parent, takeProfit, stopLoss = BracketOrder(
    'BUY', 100, 175.0,
    takeProfitPrice=185.0,
    stopLossPrice=170.0
)

for order in (parent, takeProfit, stopLoss):
    ib.placeOrder(contract, order)
```

### Trailing Stop
```python
order = Order()
order.action = 'SELL'
order.totalQuantity = 100
order.orderType = 'TRAIL'
order.trailingPercent = 2.0  # 2%
order.tif = 'GTC'
```

### Conditional Order
```python
# Trigger when SPY hits 450
trigger_contract = Stock('SPY', 'SMART', 'USD')
trigger_contract = ib.qualifyContracts(trigger_contract)[0]

condition = PriceCondition(
    condType=1,
    conId=trigger_contract.conId,
    exchange='SMART',
    isMore=True,  # Above price
    price=450.0
)

order = LimitOrder('BUY', 100, 175.0)
order.conditions = [condition]
```

### TWAP (Large Orders)
```python
order = Order()
order.action = 'BUY'
order.totalQuantity = 10000
order.orderType = 'LMT'
order.lmtPrice = 175.0
order.tif = 'DAY'
order.algoStrategy = 'Twap'
order.algoParams = [
    TagValue('startTime', '09:30:00 EST'),
    TagValue('endTime', '16:00:00 EST')
]
```

## Placing Orders

### Basic Pattern
```python
ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)

contract = Stock('AAPL', 'SMART', 'USD')
contract = ib.qualifyContracts(contract)[0]

order = LimitOrder('BUY', 100, 175.0)
trade = ib.placeOrder(contract, order)

# Wait for fill
while not trade.isDone():
    ib.sleep(0.1)

print(f"Status: {trade.orderStatus.status}")
```

### With Validation
```python
# Check buying power first
order_copy = Order(**{k: v for k, v in order.__dict__.items()})
order_copy.whatIf = True

orderState = ib.whatIfOrder(contract, order_copy)
if orderState.commission > 0:
    trade = ib.placeOrder(contract, order)
```

## Order Management

### Cancel Order
```python
ib.cancelOrder(order)
```

### Cancel All
```python
ib.reqGlobalCancel()
```

### Modify Order
```python
order.lmtPrice = 176.0
trade = ib.placeOrder(contract, order)
```

### Monitor Status
```python
def on_order_status(trade):
    print(f"Order {trade.order.orderId}: {trade.orderStatus.status}")

ib.orderStatusEvent += on_order_status
```

## Options Orders

### Single Option
```python
option = Option('SPY', '20240315', 450, 'C', 'SMART')
option = ib.qualifyContracts(option)[0]
order = LimitOrder('BUY', 10, 5.50)
trade = ib.placeOrder(option, order)
```

### Vertical Spread
```python
buy_call = Option('SPY', '20240315', 450, 'C', 'SMART')
sell_call = Option('SPY', '20240315', 460, 'C', 'SMART')
buy_call, sell_call = ib.qualifyContracts(buy_call, sell_call)

combo = Contract()
combo.symbol = 'SPY'
combo.secType = 'BAG'
combo.currency = 'USD'
combo.exchange = 'SMART'

combo.comboLegs = [
    ComboLeg(conId=buy_call.conId, ratio=1, action='BUY', exchange='SMART'),
    ComboLeg(conId=sell_call.conId, ratio=1, action='SELL', exchange='SMART')
]

order = LimitOrder('BUY', 10, 5.50)  # Debit spread
trade = ib.placeOrder(combo, order)
```

## Time In Force

```python
'DAY'    # Day order (default)
'GTC'    # Good till cancelled
'IOC'    # Immediate or cancel
'GTD'    # Good till date
'FOK'    # Fill or kill
```

## Common Patterns

### Position Entry with Protection
```python
# 1. Enter position
entry = MarketOrder('BUY', 100)
entry_trade = ib.placeOrder(contract, entry)

# 2. Wait for fill
while not entry_trade.isDone():
    ib.sleep(0.1)

if entry_trade.orderStatus.status == 'Filled':
    avg_price = entry_trade.orderStatus.avgFillPrice
    
    # 3. Set stop loss
    stop = StopOrder('SELL', 100, avg_price * 0.98)  # 2% stop
    ib.placeOrder(contract, stop)
    
    # 4. Set take profit
    target = LimitOrder('SELL', 100, avg_price * 1.05)  # 5% profit
    ib.placeOrder(contract, target)
```

### Scale In/Out
```python
# Scale in
for qty in [25, 25, 25, 25]:
    order = LimitOrder('BUY', qty, price)
    ib.placeOrder(contract, order)
    ib.sleep(300)  # 5 min between orders

# Scale out
total_position = 100
for pct in [0.25, 0.25, 0.25, 0.25]:
    qty = int(total_position * pct)
    order = LimitOrder('SELL', qty, price)
    ib.placeOrder(contract, order)
```

## Error Handling

```python
def place_order_safe(ib, contract, order):
    try:
        trade = ib.placeOrder(contract, order)
        
        # Wait with timeout
        timeout = 10
        start = time.time()
        while trade.orderStatus.status == 'PendingSubmit':
            if time.time() - start > timeout:
                ib.cancelOrder(order)
                raise TimeoutError("Order submission timeout")
            ib.sleep(0.1)
        
        return trade
    except Exception as e:
        print(f"Order failed: {e}")
        return None
```

## Best Practices

✅ Always qualify contracts first
✅ Use whatIfOrder to validate
✅ Set appropriate TIF
✅ Use limit orders in volatile markets
✅ Always have stop losses
✅ Monitor order status with events
❌ Don't use market orders on thinly traded stocks
❌ Don't forget to check buying power
❌ Don't place orders outside trading hours