# Stage 1: Base runtime image
FROM python:3.10-slim

WORKDIR /tmp

## Installing TA-Lib, required by backtrader
RUN apt-get update
RUN apt-get install -y wget tar gcc make
RUN wget https://sourceforge.net/projects/ta-lib/files/ta-lib/0.4.0/ta-lib-0.4.0-src.tar.gz
RUN tar -xzf ta-lib-0.4.0-src.tar.gz
WORKDIR /tmp/ta-lib
RUN ./configure --prefix=/usr
RUN make
RUN make install

# Install runtime dependencies
RUN pip install --upgrade pip

WORKDIR /app

# copy application code
COPY . .
ENV PYTHONPATH=src
RUN pip install -r requirements.txt

