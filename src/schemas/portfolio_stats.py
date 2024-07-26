from datetime import date
from pydantic import BaseModel

class PositionStats(BaseModel):
    ticker: str
    date: date
    units: float
    open: float
    pnl: float
    pnl_pct: float
        
class AssetStats:
    ticker: str
    price: float
    units: float
    num_positions: int
    pnl: float
    pnl_pct: float
    value: float

class PortfolioStats:
    total_invested: float
    pnl: float
    pnl_pct: float
    portfolio_value: float
    asset_stats: list[AssetStats]
    position_stats: list[PositionStats]