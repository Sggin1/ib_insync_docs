# ib_insync Documentation Repository

Comprehensive documentation collection for the **ib_insync** Python library - making Interactive Brokers API integration simple and Pythonic.

## 📚 Repository Structure

```
ib_insync_docs/
├── docs/                          # 📖 Processed Documentation (Ready to Read)
│   ├── README.md                  # Quick start guide
│   ├── ib.md                      # Complete API reference (146 KB, 4,071 lines)
│   ├── ib_insync_complete_guide.md # Comprehensive tutorial (52 KB, 1,578 lines)
│   ├── ib_insync_futures_update.md # Futures trading guide (18 KB, 522 lines)
│   ├── index.md                   # API reference index (66 KB, 892 lines)
│   ├── recipes.md                 # Code patterns and recipes
│   ├── notebooks-guide.md         # Jupyter notebooks guide
│   └── changelog.md               # Version history
│
├── inject/                        # 🔧 Raw Source Documentation
│   ├── README.md                  # Source docs guide
│   ├── *.rst                      # Original reStructuredText files
│   └── notebooks/                 # Jupyter notebook files (8 notebooks)
│       ├── basics.ipynb
│       ├── contract_details.ipynb
│       ├── ordering.ipynb
│       ├── bar_data.ipynb
│       ├── tick_data.ipynb
│       ├── market_depth.ipynb
│       ├── option_chain.ipynb
│       └── scanners.ipynb
│
└── ib-insync.pdf                  # 📄 Official documentation PDF (673 KB)
```

## 🚀 Quick Start

### For Developers & Traders

**Start here**: `docs/README.md` - Installation, quick examples, and overview

**API Reference**: `docs/ib.md` - Complete API with all classes, methods, and attributes

**Learn by Example**: `docs/notebooks-guide.md` - Interactive Jupyter tutorials

**Practical Recipes**: `docs/recipes.md` - Common patterns and best practices

### For Advanced Users

**Complete Guide**: `docs/ib_insync_complete_guide.md` - Deep dive into:
- Asynchronous programming patterns
- Single source of truth architecture
- Order placement strategies
- Live data streaming
- Event-driven processing

**Futures Trading**: `docs/ib_insync_futures_update.md` - Specialized guide for futures contracts

### For Contributors & Documentation Builders

**Raw Sources**: `inject/` folder contains:
- Original RST files from GitHub
- Complete Jupyter notebooks
- Build your own documentation versions

## 📖 Documentation Files

### Core Documentation (docs/)

| File | Size | Lines | Description |
|------|------|-------|-------------|
| **ib.md** | 144 KB | 4,071 | Complete API reference with examples |
| **ib_insync_complete_guide.md** | 52 KB | 1,578 | Comprehensive technical guide |
| **ib_insync_futures_update.md** | 18 KB | 522 | Futures-specific patterns |
| **index.md** | 66 KB | 892 | API reference index |
| **recipes.md** | 12 KB | - | Practical code recipes |
| **notebooks-guide.md** | 14 KB | - | Jupyter notebooks guide |
| **changelog.md** | 8 KB | - | Version history |

### Source Documentation (inject/)

| File | Size | Description |
|------|------|-------------|
| **README.rst** | 4.6 KB | Main project README |
| **api.rst** | 786 B | API structure |
| **recipes.rst** | 7.6 KB | Code recipes source |
| **notebooks.rst** | 1.1 KB | Notebook links |
| **changelog.rst** | 20 KB | Complete changelog |
| **8 x .ipynb files** | 225 KB | Jupyter notebooks |

## 🎯 What is ib_insync?

**ib_insync** is a Python library that simplifies interaction with Interactive Brokers' Trader Workstation API.

### Key Features

- ✅ **Linear programming** - Write sequential code without complex callbacks
- ✅ **Automatic synchronization** - State always reflects TWS/Gateway reality
- ✅ **Dual interface** - Both blocking and async methods available
- ✅ **Event-driven** - Real-time data with simple event handlers
- ✅ **Jupyter compatible** - Interactive development and analysis
- ✅ **asyncio-based** - High-performance concurrent operations

### Installation

```bash
pip install ib_insync
```

### Quick Example

```python
from ib_insync import *

# Connect to IB
ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)

# Get market data
contract = Stock('AAPL', 'SMART', 'USD')
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

# Convert to DataFrame
import pandas as pd
df = pd.DataFrame(bars)
print(df)
```

## 📚 Learning Path

### Beginners
1. Read `docs/README.md` - Quick start and installation
2. Try examples from `docs/notebooks-guide.md`
3. Explore `docs/recipes.md` for common patterns

### Intermediate
1. Study `docs/ib_insync_complete_guide.md` - Core concepts
2. Review `docs/ib.md` for specific APIs
3. Run Jupyter notebooks from `inject/notebooks/`

### Advanced
1. Deep dive into async programming patterns
2. Study futures trading guide for specialized contracts
3. Build custom solutions using API reference

## 🔗 Official Resources

- **ReadTheDocs**: https://ib-insync.readthedocs.io/
- **GitHub Repository**: https://github.com/erdewit/ib_insync
- **User Group**: https://groups.io/g/insync
- **Successor Project (ib_async)**: https://github.com/ib-api-reloaded/ib_async

## ⚠️ Important Notes

### Library Status

The original **ib_insync (v0.9.86)** remains functional but is no longer actively developed following creator Ewald de Wit's passing in March 2024.

An actively maintained successor, **ib_async**, continues development with API compatibility:
- GitHub: https://github.com/ib-api-reloaded/ib_async
- All patterns and documentation from this repository apply to both libraries

### Requirements

- Python 3.6 or higher
- TWS or IB Gateway (version 1023+) with API enabled
- Market data subscriptions for real-time data

### Not Affiliated

This library is not affiliated with Interactive Brokers Group, Inc.

## 📄 License

Licensed under simplified BSD terms.

## 🙏 Tribute

In memory of **Ewald de Wit** (1970-2024), the original creator of ib_insync, whose excellent work made algorithmic trading with Interactive Brokers accessible to Python developers worldwide. His contributions to the open-source community continue to benefit traders and developers globally.

## 🤝 Contributing

While the original ib_insync is in maintenance mode:
- Community support available through the user group
- Fork and contribute to **ib_async** for new features
- Documentation improvements welcome via pull requests

## 📞 Support

- **User Group**: https://groups.io/g/insync
- **Issues**: https://github.com/erdewit/ib_insync/issues
- **ib_async Issues**: https://github.com/ib-api-reloaded/ib_async/issues

---

**Last Updated**: November 2024
**ib_insync Version**: 0.9.86 (final release)
**Documentation Status**: Complete
