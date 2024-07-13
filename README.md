# Objective
Simplify potential stock trade analysis and decisioning using standard investment strategies and notifications

```gherkin
Given previous stakes
When today comes
Then notify me if I should buy, sell or do nothing
```

# Setup
## Installing TA-Lib
TA-Lib is required by backtrader, so it needs to be built first as per [ta-lib-python docs](https://github.com/TA-Lib/ta-lib-python?tab=readme-ov-file#linux)

```sh
wget https://sourceforge.net/projects/ta-lib/files/ta-lib/0.4.0/ta-lib-0.4.0-src.tar.gz/download
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib
./configure --prefix=/usr
make
sudo make install
```

## Clean virtual environment
```sh
make clean
```

## Create virtual environment with required dependencies

```sh
make setup
```

# CLI usage

## Advise what trades to make today
```sh
python runtime/api/cli.py trade-today
```

# Interactive usage
Start in interactive mode
```sh
python runtime/api/interactive.py
```

Type commands as you would using CLI
```sh
trade-today