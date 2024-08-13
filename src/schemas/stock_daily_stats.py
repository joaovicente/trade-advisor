from pydantic import BaseModel
from datetime import date
class StockDailyStats(BaseModel):
    date: date
    ticker: str
    close: float
    rsi: float
    rsi_ma: float
    rsi_crossover_signal: bool
    bb_top: float
    bb_mid: float
    bb_bot: float
    position: float
    pnl_pct: float

    def as_text(self, include_date=True):
        rsi_crossover_symbol = "*" if self.rsi_crossover_signal else " "
        text = (f"{self.ticker}, "
                f"close: {round(self.close, 2):7.2f}, "
                f"{rsi_crossover_symbol}rsi: {self.rsi:.2f}, "
                f"rsi-ma: {self.rsi_ma:.2f}, "
                f"bb-top: {self.bb_top:.2f}, "
                f"bb-mid: {self.bb_mid:.2f}, "
                f"bb-bot: {self.bb_bot:.2f}, "
                f"position: {self.position:.2f}, "
                f"pnl-pct: {self.pnl_pct:.2f}%"
        )
        if include_date:
            text = f"{self.date}, " + text
        return text 

    def __repr__(self):
        return f"StockDailyStats(date={self.date}, ticker={self.ticker}, close={self.close}, rsi={self.rsi}, rsi_ma={self.rsi_ma}, rsi_crossover_signal={self.rsi_crossover_signal}, bb=[{self.bb_top},{self.bb_mid},{self.bb_bot}], positions={self.positions}, pnl_pct={self.pnl_pct})"