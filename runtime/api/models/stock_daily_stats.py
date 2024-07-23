class StockDailyStats:
    def __init__(self, date, ticker, close, rsi, rsi_ma, rsi_crossover_signal, position, pnl_pct):
        self.date = date
        self.ticker = ticker
        self.close = close
        self.rsi = rsi
        self.rsi_ma = rsi_ma
        self.rsi_crossover_signal = rsi_crossover_signal
        self.position = position
        self.pnl_pct = pnl_pct

    def  as_text(self):
        rsi_crossover_symbol = "*" if self.rsi_crossover_signal else " "
        text = (f"{self.date}, "
                f"{self.ticker}, "
                f"close: {self.close:.2f}, "
                f"{rsi_crossover_symbol}rsi: {self.rsi:.2f}, "
                f"rsi-ma: {self.rsi_ma:.2f}, "
                f"position: {self.position:.2f}, "
                f"pnl-pct: {self.pnl_pct:.2f}%"
        )
        return text 

    def __repr__(self):
        return f"StockDailyStats(date={self.date}, ticker={self.ticker}, close={self.close}, rsi={self.rsi}, rsi_ma={self.rsi_ma}, rsi_crossover_signal={self.rsi_crossover_signal}, positions={self.positions}, pnl_pct={self.pnl_pct})"