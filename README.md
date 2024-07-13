# Objective
Simplify potential stock trade analysis and decisioning using standard investment strategies and notifications

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

## Setup virtual environment
```sh
make clean
make setup
```

## Install dependencies

```sh
make setup
```
