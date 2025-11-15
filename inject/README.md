# Source Documents - inject/

This folder contains **raw source documentation** files directly from the official ib_insync repository.

## Contents

### Documentation Source Files (RST Format)

These are the original reStructuredText files used to build the official documentation at https://ib-insync.readthedocs.io/

- **README.rst** - Main project README
- **api.rst** - API documentation structure
- **recipes.rst** - Code recipes and patterns
- **notebooks.rst** - Jupyter notebook links and descriptions
- **changelog.rst** - Complete version history
- **index.rst** - Documentation index/table of contents
- **code.rst** - Source code links
- **links.rst** - External links and references

### Jupyter Notebooks (notebooks/)

Complete set of interactive example notebooks from the official repository:

1. **basics.ipynb** (13 KB) - Package overview, connection, state management, contract specification
2. **contract_details.ipynb** (48 KB) - Contract lookup, qualification, and pattern matching
3. **ordering.ipynb** (13 KB) - Order placement, modification, cancellation, and monitoring
4. **bar_data.ipynb** (69 KB) - Historical and real-time bar data requests
5. **tick_data.ipynb** (12 KB) - Tick-level market data streaming
6. **market_depth.ipynb** (6.3 KB) - Order book / Level II data
7. **option_chain.ipynb** (16 KB) - Options data and Greeks calculations
8. **scanners.ipynb** (48 KB) - Market scanner subscriptions

**Total Size**: ~225 KB of notebook examples

## Source Repository

All files are sourced from the official ib_insync GitHub repository:
https://github.com/erdewit/ib_insync

## Documentation Build Process

The RST files in this folder are used with Sphinx to build the official ReadTheDocs documentation. To build locally:

```bash
# Install Sphinx
pip install sphinx sphinx-rtd-theme

# Navigate to docs directory (if you have the full repo)
cd docs/

# Build HTML documentation
make html
```

## Using the Notebooks

To run the Jupyter notebooks:

```bash
# Install requirements
pip install ib_insync jupyter pandas matplotlib

# Start Jupyter
jupyter notebook

# Navigate to inject/notebooks/ and open any notebook
```

**Important**:
- Notebooks require TWS or IB Gateway running with API enabled
- Use paper trading account for testing (port 7497)
- Market data subscriptions required for real-time data

## File Formats

- **.rst** - reStructuredText (markup language for documentation)
- **.ipynb** - Jupyter Notebook (JSON format with code cells)

## Versioning

These source files correspond to **ib_insync version 0.9.86** (final release).

## Related Folders

- **../docs/** - Processed, ready-to-read markdown documentation
- **../** - Root contains PDF and original files

## License

All source materials are from the ib_insync project, licensed under the BSD license.

Original creator: Ewald de Wit (1970-2024)
