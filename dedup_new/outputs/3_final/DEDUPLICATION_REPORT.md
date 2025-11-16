# IB_INSYNC Documentation Deduplication Report

Generated: 2025-11-16 03:11:36

## Summary

- **Original examples:** 297
- **Deduplicated examples:** 272
- **Deduplication ratio:** 8.4% reduction
- **Files processed:** 8

## Extraction Stats

- **Total files:** 8
- **Files processed:** ib_orders_reference.md, ib_data_reference.md, index.md, ib_insync_complete_guide.md, ib_insync_futures_update.md, pdf_extract.md, ib_advanced_patterns.md, ib_complete_reference.md
- **Languages:** python: 297
- **Avg examples per file:** 37.1

## Deduplication Stats

- **Total clusters:** 272
- **Singleton clusters:** 255 (no duplicates)
- **Multi-example clusters:** 17 (had duplicates)
- **Largest cluster:** 5 examples

## Cost Information

- **Total cost:** $0.0563
- **Input tokens:** 9,408.0
- **Output tokens:** 23,342.0
- **Total tokens:** 32,750.0

## Top Merged Examples

### 1.  Market Order

**Tags:** order

**Sources:** 1 original examples

```python
from ib_insync import *
order = MarketOrder('BUY', 100)
```

**Notes:** Single example, no duplicates found

---

### 2.  Limit Order

**Tags:** order

**Sources:** 1 original examples

```python
order = LimitOrder('BUY', 100, 175.50)
```

**Notes:** Single example, no duplicates found

---

### 3.  Stop Order

**Tags:** order

**Sources:** 1 original examples

```python
order = StopOrder('SELL', 100, 170.00)  # Stop loss
```

**Notes:** Single example, no duplicates found

---

### 4. Creates a bracket order with entry, take profit, and stop loss orders. The parent order is a BUY order for 100 contracts at 175.0, with profit-taking at 185.0 and stop loss at 170.0. All three orders are placed sequentially using a loop. This pattern ensures risk management by automatically setting profit targets and loss limits. Works for both stock and derivatives trading.

**Tags:** contract, order, error

**Sources:** 2 original examples

```python
parent, takeProfit, stopLoss = BracketOrder(
    'BUY', 100, 175.0,
    takeProfitPrice=185.0,
    stopLossPrice=170.0
)

for order in (parent, takeProfit, stopLoss):
    ib.placeOrder(contract, order)
```

**Notes:** Examples show different price parameters (175/185/170 vs 150/160/145) demonstrating the pattern works with any price levels. Example 1 includes 'error' tag highlighting potential error handling considerations.

---

### 5. Creates a trailing stop order that tracks price movements by percentage. Specifies SELL action, 100 shares, 2% trailing offset, and Good-Til-Canceled duration. Includes order placement example requiring a valid contract object. Suitable for percentage-based trailing stop loss strategies.

**Tags:** order, contract

**Sources:** 2 original examples

```python
order = Order()
order.action = 'SELL'
order.totalQuantity = 100
order.orderType = 'TRAIL'
order.trailingPercent = 2.0  # Trail by 2%
order.tif = 'GTC'

# Requires valid contract object
# trade = ib.placeOrder(contract, order)
```

**Notes:** Example 2 includes order placement with contract while Example 1 stops at order configuration. Both use identical order parameters. Actual implementation requires valid contract object for placement.

---

### 6.  Conditional Order

**Tags:** contract, order

**Sources:** 1 original examples

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

**Notes:** Single example, no duplicates found

---

### 7. Creates a TWAP (Time-Weighted Average Price) order for large orders. Specifies limit price, duration (09:30-16:00 EST), and allows order execution past the end time. Requires order placement with a valid contract. Combines core order configuration with optional past-end-time allowance parameter.

**Tags:** order, contract, TWAP

**Sources:** 2 original examples

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
    TagValue('endTime', '16:00:00 EST'),
    TagValue('allowPastEndTime', '1')
]

# Requires contract definition before placement:
# trade = ib.placeOrder(contract, order)
```

**Notes:** Example 2 adds 'allowPastEndTime=1' parameter and demonstrates order placement. Example 1 omits these but shows basic structure. Both use same core TWAP configuration.

---

### 8.  Basic Pattern

**Tags:** connect, contract, order

**Sources:** 1 original examples

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

**Notes:** Single example, no duplicates found

---

### 9.  With Validation

**Tags:** contract, order

**Sources:** 1 original examples

```python
# Check buying power first
order_copy = Order(**{k: v for k, v in order.__dict__.items()})
order_copy.whatIf = True

orderState = ib.whatIfOrder(contract, order_copy)
if orderState.commission > 0:
    trade = ib.placeOrder(contract, order)
```

**Notes:** Single example, no duplicates found

---

### 10.  Cancel Order

**Tags:** order

**Sources:** 1 original examples

```python
ib.cancelOrder(order)
```

**Notes:** Single example, no duplicates found

---

