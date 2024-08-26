# Objective
Simplify potential stock trade analysis and decisioning using standard investment strategies and notifications

```gherkin
Given previous positions and list of stock to watch
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

First setup virtual environment and path
```sh
source .env
source .venv/bin/activate
```

## Advise what trades to make today

### Supplying existing positions using `--position`
By default will use open position tickers, which are by default read in `./open_position.csv`

```sh
# Auto sourced positions
python src/cli/cli.py trade-today
```
To provide open positions explicitly using CLI you can use the `--position`, abreviated to `-p` supplying value as CSV string as follows `-p {date},{ticker},{size},{price}`

```sh
# Positions explicitly supplied in CLI 
python src/cli/cli.py trade-today \
    -p 2024-07-18,META,2.09692,476.89\
    -p 2024-07-18,GOOG,5.56917,179.56\
    -p 2024-07-18,NVDA,8.28706,120.67\
    -p 2024-07-18,AMZN,2.68962,185.90\
    -p 2024-07-18,MSFT,0.5328,438.16
```

To add other stock to advise purchases on you can use the tickers, given comma separated TICKERS 

### Defining selected investments using `--tickers`

```sh
# Single ticker
python src/cli/cli.py trade-today --tickers SNOW
```

```sh
# Multiple tickers
python src/cli/cli.py trade-today --tickers AAPL,ABBV,ADBE,AMD,AMZN,AVGO,BAC,BRK-B,COST,CRM,CVX,GOOG,HD,JNJ,JPM,KO,LLY,MA,META,MRK,MSFT,NFLX,NVDA,ORCL,PEP,PFE,PG,TMO,TSLA,UNH,V,WMT,XOM
```

### Using both `--positions` and `--tickers`
```sh
python src/cli/cli.py trade-today --tickers AAPL,ABBV,ADBE,AMD,AMZN,AVGO,BAC,BRK-B,COST,CRM,CVX,GOOG,HD,JNJ,JPM,KO,LLY,MA,META,MRK,MSFT,NFLX,NVDA,ORCL,PEP,PFE,PG,TMO,TSLA,UNH,V,WMT,XOM \
    -p 2024-07-18,META,2.09692,476.89\
    -p 2024-07-18,GOOG,5.56917,179.56\
    -p 2024-07-18,NVDA,8.28706,120.67\
    -p 2024-07-18,AMZN,2.68962,185.90\
    -p 2024-07-18,MSFT,0.5328,438.16
```

### Test with a previous date

For testing it is useful to test trade advice for a past date. You can to it using `--today yyyy-mm-dd` as follows 
```sh
python src/cli/cli.py trade-today --tickers SNOW --today 2024-05-31
```

## See portfolio stats

```sh
# Default positions read from ./open_position.csv
python src/cli/cli.py portfolio-stats
```

```sh
python src/cli/cli.py portfolio-stats \
    -p 2024-07-18,META,2.09692,476.89\
    -p 2024-07-18,GOOG,5.56917,179.56\
    -p 2024-07-18,NVDA,8.28706,120.67\
    -p 2024-07-18,AMZN,2.68962,185.90\
    -p 2024-07-18,MSFT,0.5328,438.16
```

```sh
Portfolio on 2024-07-28: total invested: 3733.45, portfolio_value: 3570.32, pnl: -163.13, pnl_pct: -4.37%
MSFT: units: 0.53, price: 425.27, amount:   233.45, value:   226.58, pnl:  -6.87, pnl_pct:  -2.94%
AMZN: units: 2.69, price: 182.50, amount:   500.00, value:   490.86, pnl:  -9.14, pnl_pct:  -1.83%
META: units: 2.10, price: 465.70, amount:  1000.00, value:   976.54, pnl: -23.46, pnl_pct:  -2.35%
GOOG: units: 5.57, price: 168.68, amount:  1000.00, value:   939.41, pnl: -60.59, pnl_pct:  -6.06%
NVDA: units: 8.29, price: 113.06, amount:  1000.00, value:   936.94, pnl: -63.06, pnl_pct:  -6.31%
```


# Interactive usage
Start in interactive mode
```sh
python src/cli/interactive.py
```

Type commands as you would using CLI
```sh
trade-today
```

```sh
portfolio-stats
```

# Docker 

## Build
```sh
docker build -t trade-advisor .
```

## Run
```sh
docker run -it trade-advisor python /app/src/cli/cli.py trade-today
```

# References

* [Backtrader](https://www.backtrader.com/docu/quickstart/quickstart/#using-the-platform) for backtesting
* [TA-Lib](https://ta-lib.org/) and [ta-lib-python](https://github.com/ta-lib/ta-lib-python) for built-in technical analysis [indicators](https://ta-lib.org/functions/) such as RMI (Relative Strength Index)
* [Click](https://click.palletsprojects.com) to expose CLI
* [Data Science Cohort RSI data strategy](https://github.com/Worlddatascience/DataScienceCohort/blob/refs%2Fheads%2Fmaster/9_How_to_Backtest_a_Relative_Strength_index_Strategy%C2%B6.ipynb)
* [The Bollinger Bands + RSI Trading Strategy](https://blackwellglobal.com/the-bollinger-bands-rsi-trading-strategy/)
