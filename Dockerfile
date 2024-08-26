FROM python:3.10-slim

## Installing TA-Lib, required by backtrader
WORKDIR /tmp
RUN apt-get update
RUN apt-get install -y wget tar gcc make
RUN wget https://sourceforge.net/projects/ta-lib/files/ta-lib/0.4.0/ta-lib-0.4.0-src.tar.gz
RUN tar -xzf ta-lib-0.4.0-src.tar.gz
WORKDIR /tmp/ta-lib
RUN ./configure --prefix=/usr
RUN make
RUN make install

# Copy and build application code
WORKDIR /app
COPY . .
ENV PYTHONPATH=src
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

