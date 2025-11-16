# ib_insync Futures Trading Guide - Updated 2025

## Accurate Futures Contract Qualification

When working with futures contracts in ib_insync, accurate exchange specification is critical. Here's the current correct approach:

```python
from ib_insync import *

# Connect to IB
ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)

# Correct approach for E-mini S&P 500 futures
es_contract = Future(symbol='ES', lastTradeDateOrContractMonth='202506', exchange='CME')

# Correct approach for Micro E-mini Nasdaq-100 futures
mnq_contract = Future(symbol='MNQ', lastTradeDateOrContractMonth='202506', exchange='CME')

# Correct approach for Crude Oil futures
cl_contract = Future(symbol='CL', lastTradeDateOrContractMonth='202506', exchange='NYMEX')

# Qualify the contracts
qualified_contracts = ib.qualifyContracts(es_contract, mnq_contract, cl_contract)
```

## Exchange Corrections for Common Futures

| Product | Correct Exchange | Incorrect/Outdated Exchange |
|---------|------------------|----------------------------|
| ES, NQ, MES, MNQ | CME | GLOBEX |
| CL, GC, SI | NYMEX | GLOBEX |
| ZB, ZN, ZF | CBOT | ECBOT |
| 6E, 6A, 6B | CME | GLOBEX |

## Single Source of Truth for Contract Specifications

For real-time futures trading, always fully qualify your contracts to ensure proper execution:

```python
def get_qualified_futures_contract(ib, symbol, expiry, exchange):
    """Get a fully qualified futures contract ready for trading"""
    contract = Future(symbol=symbol, 
                     lastTradeDateOrContractMonth=expiry,
                     exchange=exchange)
    
    # Request complete contract details
    qualified = ib.qualifyContracts(contract)
    
    if not qualified:
        print(f"ERROR: Could not qualify {symbol} contract")
        return None
        
    # Return the fully qualified contract
    return qualified[0]

# Example usage
es_contract = get_qualified_futures_contract(ib, 'ES', '202506', 'CME')
print(f"ConId: {es_contract.conId}, LocalSymbol: {es_contract.localSymbol}")
```

## Handling Contract Month Codes

Modern futures trading requires understanding the contract month codes:

| Month | Code | Example |
|-------|------|---------|
| January | F | ESF6 (ES Jan 2026) |
| February | G | ESG6 (ES Feb 2026) |
| March | H | ESH6 (ES Mar 2026) |
| April | J | ESJ6 (ES Apr 2026) |
| May | K | ESK6 (ES May 2026) |
| June | M | ESM6 (ES Jun 2026) |
| July | N | ESN6 (ES Jul 2026) |
| August | Q | ESQ6 (ES Aug 2026) |
| September | U | ESU6 (ES Sep 2026) |
| October | V | ESV6 (ES Oct 2026) |
| November | X | ESX6 (ES Nov 2026) |
| December | Z | ESZ6 (ES Dec 2026) |

```python
def get_contract_by_symbol(ib, local_symbol):
    """Get contract using local symbol (e.g., 'ESM6')"""
    # Parse the local symbol
    root = ''.join([c for c in local_symbol if c.isalpha()])
    suffix = ''.join([c for c in local_symbol if not c.isalpha()])
    
    # Extract month code and year
    month_code = suffix[0] if len(suffix) > 0 else ''
    year_code = suffix[1:] if len(suffix) > 1 else ''
    
    # Create generic contract
    contract = Contract()
    contract.secType = 'FUT'
    contract.symbol = root
    contract.exchange = get_exchange_for_symbol(root)  # Helper function
    contract.localSymbol = local_symbol
    
    # Qualify the contract
    qualified = ib.qualifyContracts(contract)
    return qualified[0] if qualified else None

def get_exchange_for_symbol(symbol):
    """Get correct exchange for common futures symbols"""
    exchanges = {
        'ES': 'CME', 'MES': 'CME', 'NQ': 'CME', 'MNQ': 'CME',
        'RTY': 'CME', 'M2K': 'CME', 'YM': 'CBOT', 'MYM': 'CBOT',
        'CL': 'NYMEX', 'GC': 'NYMEX', 'SI': 'NYMEX', 'HG': 'NYMEX',
        'ZB': 'CBOT', 'ZN': 'CBOT', 'ZF': 'CBOT', 'ZT': 'CBOT',
        '6E': 'CME', '6A': 'CME', '6B': 'CME', '6J': 'CME'
    }
    return exchanges.get(symbol, 'SMART')
```

## Complex Order Types for Futures

For futures trading, complex order types like OCO and trailing stops require careful setup:

```python
# Trailing stop for ES futures
def place_es_trailing_stop(ib, action, quantity, trail_amount):
    """Place a trailing stop order for ES futures"""
    # Get current front month ES contract
    es = get_front_month_contract(ib, 'ES', 'CME')
    
    # Create trailing stop order
    order = Order()
    order.action = action  # 'BUY' or 'SELL'
    order.orderType = 'TRAIL'
    order.totalQuantity = quantity
    order.auxPrice = trail_amount  # Trail amount in points
    
    # Place the order
    trade = ib.placeOrder(es, order)
    return trade

# Market-Limit OCO for MNQ futures
def place_mnq_market_limit_oco(ib, action, quantity, limit_price):
    """Place a market-limit OCO order for MNQ futures"""
    # Get current front month MNQ contract
    mnq = get_front_month_contract(ib, 'MNQ', 'CME')
    
    # Create OCO orders
    market_order = MarketOrder(action, quantity)
    limit_order = LimitOrder(action, quantity, limit_price)
    
    # Set up OCO group
    oca_group = f"MNQ_OCO_{int(time.time())}"  # Unique group ID
    
    market_order.ocaGroup = oca_group
    market_order.ocaType = 2  # Proportional
    
    limit_order.ocaGroup = oca_group
    limit_order.ocaType = 2
    
    # Place orders
    trade1 = ib.placeOrder(mnq, market_order)
    trade2 = ib.placeOrder(mnq, limit_order)
    
    return [trade1, trade2]
```

## Efficient Futures Data Streaming

For live futures data, proper subscription management is essential:

```python
class FuturesDataManager:
    """Manage real-time data for multiple futures contracts"""
    
    def __init__(self, ib):
        self.ib = ib
        self.tickers = {}
        self.active_contracts = set()
        
    def subscribe(self, symbol, exchange='CME'):
        """Subscribe to real-time market data for a futures contract"""
        # Get front month contract
        contract = get_front_month_contract(self.ib, symbol, exchange)
        
        if not contract:
            print(f"Error: Could not find front month contract for {symbol}")
            return None
            
        # Request market data
        ticker = self.ib.reqMktData(contract, '', False, False)
        
        # Store references
        self.tickers[symbol] = ticker
        self.active_contracts.add(contract)
        
        return ticker
        
    def get_price(self, symbol):
        """Get current price for a subscribed symbol"""
        if symbol not in self.tickers:
            return None
            
        ticker = self.tickers[symbol]
        
        # Use last or midpoint price
        if ticker.last:
            return ticker.last
        elif ticker.bid and ticker.ask:
            return (ticker.bid + ticker.ask) / 2
        else:
            return None
    
    def get_contracts_expiring_soon(self, days_threshold=10):
        """Get list of contracts expiring soon"""
        expiring_soon = []
        now = datetime.now()
        
        for contract in self.active_contracts:
            expiry_str = contract.lastTradeDateOrContractMonth
            
            if len(expiry_str) == 8:  # YYYYMMDD format
                expiry = datetime.strptime(expiry_str, '%Y%m%d')
            else:  # YYYYMM format
                expiry = datetime.strptime(f"{expiry_str}01", '%Y%m%d')
                
            days_to_expiry = (expiry - now).days
            
            if days_to_expiry <= days_threshold:
                expiring_soon.append((contract, days_to_expiry))
                
        return expiring_soon
        
    def cleanup(self):
        """Unsubscribe from all market data"""
        for contract in self.active_contracts:
            self.ib.cancelMktData(contract)
            
        self.tickers.clear()
        self.active_contracts.clear()
```

## Working with Continuous Futures Contracts

For continuous futures analysis, use a combination of reqHistoricalData and dynamic front-month tracking:

```python
def get_continuous_futures_data(ib, symbol, exchange, duration='1 Y', bar_size='1 day'):
    """Get historical data for continuous futures contract"""
    # Create a ContFuture for historical data
    contract = ContFuture(symbol, exchange)
    ib.qualifyContracts(contract)
    
    # Request historical data
    bars = ib.reqHistoricalData(
        contract,
        endDateTime='',
        durationStr=duration,
        barSizeSetting=bar_size,
        whatToShow='TRADES',
        useRTH=True
    )
    
    return bars

# Get front month based on volume/open interest
def get_most_liquid_contract(ib, symbol, exchange):
    """Get the most liquid contract based on volume and open interest"""
    # Get all active contracts for this symbol
    contract = Future(symbol, exchange=exchange)
    details_list = ib.reqContractDetails(contract)
    
    if not details_list:
        return None
    
    # Filter out expired contracts
    now = datetime.now()
    active_contracts = []
    
    for details in details_list:
        expiry_str = details.contract.lastTradeDateOrContractMonth
        
        if len(expiry_str) == 8:
            expiry = datetime.strptime(expiry_str, '%Y%m%d')
        else:
            expiry = datetime.strptime(f"{expiry_str}01", '%Y%m%d')
            
        if expiry > now:
            active_contracts.append(details.contract)
    
    if not active_contracts:
        return None
    
    # Get volume data for each contract
    contract_data = []
    
    for contract in active_contracts:
        ticker = ib.reqMktData(contract, '100,101', False, False)  # Request volume and OI
        ib.sleep(1)  # Allow data to populate
        
        contract_data.append({
            'contract': contract,
            'volume': ticker.volume or 0,
            'openInterest': ticker.openInterest or 0
        })
        
        # Cancel the market data request
        ib.cancelMktData(contract)
    
    # Sort by combined volume and open interest
    contract_data.sort(key=lambda x: x['volume'] + x['openInterest'], reverse=True)
    
    # Return the most liquid contract
    return contract_data[0]['contract'] if contract_data else None
```

## Production-Ready Futures Trading System

Here's a more comprehensive structure for a futures trading system:

```python
class FuturesTradingSystem:
    """Complete futures trading system with proper state management"""
    
    def __init__(self, host='127.0.0.1', port=7497, client_id=1):
        self.ib = IB()
        self.host = host
        self.port = port
        self.client_id = client_id
        
        self.active_contracts = {}  # symbol -> contract
        self.active_orders = {}     # orderId -> order
        self.active_positions = {}  # symbol -> position
        
        # Setup logger
        self.logger = self._setup_logger()
        
    def _setup_logger(self):
        logger = logging.getLogger('FuturesTradingSystem')
        logger.setLevel(logging.INFO)
        
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
        
    def connect(self):
        """Connect to IB and initialize state"""
        try:
            self.ib.connect(self.host, self.port, clientId=self.client_id)
            self.logger.info(f"Connected to IB ({self.host}:{self.port})")
            
            # Setup event handlers
            self.ib.errorEvent += self._handle_error
            self.ib.positionEvent += self._handle_position
            self.ib.orderStatusEvent += self._handle_order_status
            
            # Initialize positions
            self._update_positions()
            
            return True
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            return False
    
    def _update_positions(self):
        """Update current positions"""
        positions = self.ib.positions()
        
        for position in positions:
            if position.contract.secType == 'FUT':
                symbol = position.contract.symbol
                self.active_positions[symbol] = position
                self.logger.info(f"Current position: {symbol}: {position.position}")
    
    def _handle_position(self, position):
        """Handle position updates"""
        if position.contract.secType == 'FUT':
            symbol = position.contract.symbol
            self.active_positions[symbol] = position
            self.logger.info(f"Position update: {symbol}: {position.position}")
    
    def _handle_order_status(self, trade):
        """Handle order status updates"""
        orderId = trade.order.orderId
        status = trade.orderStatus.status
        
        self.logger.info(f"Order {orderId} status: {status}")
        
        # Store active orders
        if status in ['Submitted', 'PreSubmitted', 'PendingSubmit']:
            self.active_orders[orderId] = trade
        # Remove completed orders
        elif status in ['Filled', 'Cancelled', 'Inactive']:
            if orderId in self.active_orders:
                del self.active_orders[orderId]
    
    def _handle_error(self, reqId, errorCode, errorString, contract):
        """Handle error events"""
        self.logger.error(f"Error {errorCode}: {errorString}")
        
        # Handle connection issues
        if errorCode in [1100, 1101, 1102]:
            self.logger.critical("Connection issue detected!")
    
    def get_contract(self, symbol, expiry, exchange):
        """Get a fully qualified futures contract"""
        contract_key = f"{symbol}_{expiry}_{exchange}"
        
        # Use cached contract if available
        if contract_key in self.active_contracts:
            return self.active_contracts[contract_key]
            
        # Otherwise qualify a new one
        contract = Future(symbol=symbol, 
                         lastTradeDateOrContractMonth=expiry,
                         exchange=exchange)
        
        qualified = self.ib.qualifyContracts(contract)
        
        if not qualified:
            self.logger.error(f"Failed to qualify contract: {symbol} {expiry}")
            return None
            
        qualified_contract = qualified[0]
        self.active_contracts[contract_key] = qualified_contract
        
        return qualified_contract
    
    def place_market_order(self, symbol, expiry, exchange, action, quantity):
        """Place market order for futures contract"""
        contract = self.get_contract(symbol, expiry, exchange)
        
        if not contract:
            return None
            
        order = MarketOrder(action, quantity)
        trade = self.ib.placeOrder(contract, order)
        
        self.logger.info(f"Placed {action} market order for {quantity} {symbol}")
        return trade
    
    def place_limit_order(self, symbol, expiry, exchange, action, quantity, price):
        """Place limit order for futures contract"""
        contract = self.get_contract(symbol, expiry, exchange)
        
        if not contract:
            return None
            
        order = LimitOrder(action, quantity, price)
        trade = self.ib.placeOrder(contract, order)
        
        self.logger.info(f"Placed {action} limit order for {quantity} {symbol} @ {price}")
        return trade
    
    def place_bracket_order(self, symbol, expiry, exchange, action, quantity, 
                          entry_price, profit_price, stop_price):
        """Place bracket order for futures contract"""
        contract = self.get_contract(symbol, expiry, exchange)
        
        if not contract:
            return None
            
        # Create bracket orders
        bracket = self.ib.bracketOrder(
            action,
            quantity,
            entry_price,
            profit_price,
            stop_price
        )
        
        # Place all orders
        trades = []
        for order in bracket:
            trade = self.ib.placeOrder(contract, order)
            trades.append(trade)
        
        self.logger.info(f"Placed bracket order for {quantity} {symbol}")
        return trades
    
    def cancel_all_orders(self):
        """Cancel all open orders"""
        open_trades = self.ib.openTrades()
        for trade in open_trades:
            if not trade.isDone():
                self.ib.cancelOrder(trade.order)
                self.logger.info(f"Cancelled order {trade.order.orderId}")
    
    def get_position(self, symbol):
        """Get current position for symbol"""
        return self.active_positions.get(symbol)
    
    def close_position(self, symbol):
        """Close position for symbol"""
        position = self.get_position(symbol)
        
        if not position or position.position == 0:
            self.logger.info(f"No position to close for {symbol}")
            return None
        
        # Create closing order
        action = 'SELL' if position.position > 0 else 'BUY'
        quantity = abs(position.position)
        
        return self.place_market_order(
            symbol,
            position.contract.lastTradeDateOrContractMonth,
            position.contract.exchange,
            action,
            quantity
        )
    
    def run(self):
        """Run the system indefinitely"""
        try:
            self.ib.run()
        except KeyboardInterrupt:
            self.logger.info("Shutting down...")
        finally:
            # Cleanup on exit
            self.cancel_all_orders()
            self.ib.disconnect()
            self.logger.info("Disconnected from IB")
```
