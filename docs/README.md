# IB-insync Documentation Collection

## Overview

IB-insync is a Python library designed to simplify interaction with Interactive Brokers' Trader Workstation API. The project aims to "make working with the Trader Workstation API from Interactive Brokers as easy as possible."

This repository contains comprehensive documentation gathered from official sources for the ib_insync library.

## Key Features

- **Linear, straightforward programming approach** - Write sequential code without complex callback patterns
- **Automatic synchronization** with TWS or IB Gateway applications
- **Asynchronous framework** built on asyncio and eventkit for high-performance applications
- **Jupyter notebook compatibility** for live data analysis and interactive development
- **Dual interface** - Both blocking and async methods available

## Installation & Requirements

### Installation
```bash
pip install ib_insync
```

### Prerequisites
- Python 3.6 or higher
- Active TWS or IB Gateway (version 1023+) with enabled API port
- No separate ibapi package needed (ib_insync includes everything)

## Quick Start Example

```python
from ib_insync import *

# Connect to IB Gateway or TWS
ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)

# Create a contract
contract = Stock('AAPL', 'SMART', 'USD')
ib.qualifyContracts(contract)

# Request market data
ticker = ib.reqMktData(contract)
ib.sleep(2)
print(f"Last price: {ticker.last}")

# Get historical data
bars = ib.reqHistoricalData(
    contract,
    endDateTime='',
    durationStr='30 D',
    barSizeSetting='1 hour',
    whatToShow='TRADES',
    useRTH=True
)

# Convert to pandas DataFrame
import pandas as pd
df = pd.DataFrame(bars)
print(df)

# Disconnect
ib.disconnect()
```

## Documentation Files in This Repository

### Core Documentation
- **[ib_insync_complete_guide.md](ib_insync_complete_guide.md)** - Comprehensive technical guide covering:
  - Asynchronous programming with ib_insync
  - Single source of truth implementation
  - Order placement patterns and examples
  - Contract qualification for futures
  - Live data stream handling

- **[ib_insync_futures_update.md](ib_insync_futures_update.md)** - Specialized guide for futures trading

- **[ib.md](ib.md)** - Complete API reference with all classes, methods, and attributes

- **[index.md](index.md)** - Documentation index and table of contents

### Additional Resources
- **[recipes.md](recipes.md)** - Practical code recipes and patterns
- **[notebooks-guide.md](notebooks-guide.md)** - Guide to Jupyter notebooks with examples
- **[changelog.md](changelog.md)** - Version history and updates
- **[ib-insync.pdf](ib-insync.pdf)** - Official documentation in PDF format

## Official Resources

- **ReadTheDocs**: https://ib-insync.readthedocs.io/
- **GitHub Repository**: https://github.com/erdewit/ib_insync
- **User Group**: https://groups.io/g/insync
- **Successor Project (ib_async)**: https://github.com/ib-api-reloaded/ib_async

## Important Notes

### Library Status
The original ib_insync (v0.9.86) remains functional but is no longer actively developed following its creator Ewald de Wit's passing in March 2024. An actively maintained successor, **ib_async**, continues development under the ib-api-reloaded organization with API compatibility. Both libraries share the same core patterns and documentation applies to both.

### Not Affiliated
This library is not affiliated with Interactive Brokers Group, Inc.

## License

Licensed under simplified BSD terms.

## Tribute

In memory of Ewald de Wit, the original creator of ib_insync, whose excellent work made algorithmic trading with Interactive Brokers accessible to Python developers worldwide.
