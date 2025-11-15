# Changelog

Complete version history of ib_insync from version 0.6.0 through 0.9.86.

---

## Version 0.9.x Series (Latest)

### Version 0.9.86 (Latest)
- Fixed account summary tag

### Version 0.9.85
- Socket protocol adjustments
- Bug fixes and stability improvements

### Version 0.9.84
- Additional protocol refinements
- Performance enhancements

### Version 0.9.83
- **WSH (Wall Street Horizon) request support** - Added support for querying corporate events
- Enhanced event data handling

### Version 0.9.82
- Bug fixes
- Minor improvements

### Version 0.9.81
- Protocol updates
- Stability improvements

### Version 0.9.80
- Enhanced error handling
- Connection stability improvements

---

## Version 0.8.x Series

### Major Features Introduced in 0.8 Series

**TickByTick Support**
- Most granular level of market data
- Individual tick streaming
- Support for Last, BidAsk, AllLast, and MidPoint tick types

**Automatic Request Throttling**
- Built-in rate limiting to prevent exceeding API limits
- Automatically maintains compliance with 45 requests/second limit
- Compatible with TWS/Gateway 974+

**Flex Reports**
- Financial statement and activity report generation
- Automated report retrieval
- Structured data access for account analysis

**Conditional Orders**
- Support for order conditions
- Price, time, margin, execution, and volume conditions
- Complex order logic capabilities

**Enhanced Event Handling**
- Improved event system for real-time updates
- Better error event propagation
- Ticker-specific events

**Additional Features**:
- Multi-account support enhancements
- PnL (Profit & Loss) calculation methods
- Real-time bar streaming improvements
- Historical tick data requests
- Enhanced market data subscriptions

---

## Version 0.7.x Series

### Major Features Introduced in 0.7 Series

**Order Book (DOM - Depth of Market)**
- Level II market data support
- Bid/ask depth streaming
- Real-time order book updates via `reqMktDepth()`

**Request Method Additions**:
- Account summary requests
- Position updates
- Contract details enhancements
- Historical data improvements

**Contract Types**:
- Cryptocurrency support
- Additional security types
- Enhanced futures contract handling

**Event System**:
- Expanded event coverage
- Better event filtering
- Improved callback mechanisms

---

## Version 0.6.x Series

### Version 0.6.0 (Initial Release)
- **Project Launch** - First public release of ib_insync
- Basic IB API wrapper functionality
- Synchronous and asynchronous interfaces
- Contract definitions (Stock, Option, Future, Forex, etc.)
- Order placement and management
- Market data requests
- Historical data retrieval
- Position and account management
- Event-driven architecture using eventkit
- asyncio-based networking
- Jupyter notebook compatibility

---

## Feature Timeline Summary

### Market Data Features
- **0.6.0**: Basic market data requests (`reqMktData`)
- **0.7.x**: Order book/market depth (`reqMktDepth`)
- **0.8.x**: Tick-by-tick data (`reqTickByTickData`)
- **0.8.x**: Real-time bars streaming
- **0.8.x**: Historical tick data
- **0.9.x**: Enhanced data streaming

### Order Management
- **0.6.0**: Basic order types (Market, Limit, Stop)
- **0.7.x**: Bracket orders
- **0.8.x**: Conditional orders
- **0.8.x**: Order conditions (Price, Time, Margin, etc.)
- **0.8.x**: WhatIf order analysis

### Account & Portfolio
- **0.6.0**: Basic position and account value requests
- **0.7.x**: Account summary subscriptions
- **0.8.x**: Multi-account support
- **0.8.x**: PnL calculations
- **0.8.x**: Flex report integration

### Contract Types
- **0.6.0**: Stock, Option, Future, Forex, Bond
- **0.7.x**: Cryptocurrency support
- **0.7.x**: Continuous futures
- **0.8.x**: Additional security types
- **0.9.x**: Enhanced contract qualification

### Infrastructure
- **0.6.0**: asyncio integration, eventkit events
- **0.7.x**: Event system enhancements
- **0.8.x**: Automatic request throttling
- **0.8.x**: Qt framework support (PyQt5, PySide2)
- **0.9.x**: WSH event data support
- **0.9.x**: Protocol updates and stability

### Data Analysis
- **0.6.0**: Pandas DataFrame conversion
- **0.6.0**: Jupyter notebook support
- **0.7.x**: Enhanced data structures
- **0.8.x**: Improved data formatting

---

## Notable Bug Fixes by Version

### 0.9.x Series
- Fixed account summary tag issues
- Resolved socket protocol edge cases
- Improved connection stability
- Enhanced error handling

### 0.8.x Series
- Fixed event loop integration issues
- Resolved memory leaks in long-running applications
- Corrected tick-by-tick subscription handling
- Fixed contract qualification edge cases

### 0.7.x Series
- Resolved order book update issues
- Fixed historical data request edge cases
- Corrected timezone handling
- Improved error message clarity

---

## Migration Notes

### Upgrading to 0.9.x
- Account summary API changes - verify tag usage
- Socket protocol updates may affect low-level usage
- WSH support requires updated TWS/Gateway version

### Upgrading to 0.8.x
- Automatic throttling is now enabled by default (requires TWS 974+)
- Event system changes may require handler updates
- Tick-by-tick has 3-subscription limit

### Upgrading from 0.6.x to 0.7.x
- Market depth methods now available
- New contract types may require qualification
- Enhanced event coverage may trigger additional callbacks

---

## Deprecation Notices

As of version 0.9.86:
- No current deprecations
- Library is in maintenance mode following creator's passing
- Consider migrating to **ib_async** for active development

---

## Version Requirements

### Python Version
- **0.6.x - 0.9.x**: Python 3.6 or higher
- Recommended: Python 3.8+ for best performance

### TWS/IB Gateway Version
- **Minimum**: TWS/Gateway 1023
- **Recommended**: Latest stable version
- **Required for tick-by-tick**: TWS 974+
- **Required for auto-throttling**: TWS 974+
- **Required for WSH events**: TWS with WSH support

### Dependencies
- **eventkit**: Event system (included)
- **asyncio**: Python standard library (3.6+)
- **nest_asyncio**: For Jupyter compatibility (optional)
- **pandas**: For DataFrame conversion (optional)
- **PyQt5/PySide2**: For Qt integration (optional)

---

## Future Development

**Important Note**: The original ib_insync (v0.9.86) is no longer actively developed following the creator Ewald de Wit's passing in March 2024.

### Actively Maintained Fork: ib_async

For continued development and new features, consider migrating to:
- **GitHub**: https://github.com/ib-api-reloaded/ib_async
- **Compatibility**: API-compatible with ib_insync
- **Features**: All ib_insync patterns and documentation apply
- **Status**: Actively maintained with bug fixes and enhancements

---

## Contributing

While the original ib_insync is in maintenance mode:
- Bug reports can be filed on the original GitHub repository
- Community support available through the user group
- Fork and contribute to ib_async for new features

---

## Resources

- **GitHub**: https://github.com/erdewit/ib_insync
- **Documentation**: https://ib-insync.readthedocs.io/
- **User Group**: https://groups.io/g/insync
- **Successor (ib_async)**: https://github.com/ib-api-reloaded/ib_async

---

## Acknowledgments

This library was created and maintained by **Ewald de Wit** (1970-2024), whose excellent work made algorithmic trading with Interactive Brokers accessible to Python developers worldwide. His contributions to the open-source community continue to benefit traders and developers globally.

---

*Last updated: Version 0.9.86 (Latest stable release)*
