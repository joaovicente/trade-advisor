from datetime import date
from typing import List
from pydantic import BaseModel, Field

class PositionStats(BaseModel):
    ticker: str = Field(description='position stock ticker (e.g. AMZN)')
    date: date
    units: float = Field(description='number of units of stock in this position')
    open: float = Field(description='price when stock was purchased')
    amount: float = Field(description='currency amount used to create this position')
    value: float = Field(description='worth of this position')
    pnl: float = Field(description='absolute profit and loss for this position')
    pnl_pct: float = Field(description='percentage profit and loss for this position')
        
class AssetStats(BaseModel):
    ticker: str = Field(description='asset stock ticker (e.g. AMZN)')
    price: float = Field(description='current price of this stock')
    units: float = Field(description='number of units owned for this stock across multiple positions')
    num_positions: int = Field(description='number of positions on this stock')
    amount: float = Field(description='currency spent on this stock open positions')
    value: float = Field(description='worth of all positions for this stock')
    pnl: float = Field(description='absolute profit and loss for this asset, across all stock positions')
    pnl_pct: float = Field(description='percentage profit and loss for this asset, accross all stock positions')

class PortfolioStats(BaseModel):
    total_invested: float = Field(description='total funds invested across all assets')
    pnl: float = Field(description='absolute profit and loss across all assets')
    pnl_pct: float = Field(description='absolute profit and loss across all assets')
    portfolio_value: float = Field(description='worth of all assets')
    asset_stats_list: List[AssetStats] = Field(description='assets list')
    position_stats_list: List[PositionStats] = Field(description='position stats list')
    
    def portfolio_as_text(self):
        text = (
            f"total invested: {self.total_invested:.2f}, "
            f"portfolio_value: {self.portfolio_value:.2f}, "
            f"pnl: {self.pnl:.2f}, "
            f"pnl_pct: {self.pnl_pct:.2f}%"
        )
        return text
    
    def assets_as_text(self):
        text = ""
        for asset_stats in sorted(self.asset_stats_list, key=lambda x: x.pnl, reverse=True):
            text += (
                f"{asset_stats.ticker}: "
                #f"num_positions: {asset_stats.num_positions}, "
                f"units: {asset_stats.units:.2f}, "
                f"price: {asset_stats.price:.2f}, "
                f"amount: {asset_stats.amount:8.2f}, "
                f"value: {asset_stats.value:8.2f}, "
                f"pnl: {asset_stats.pnl:6.2f}, "
                f"pnl_pct: {asset_stats.pnl_pct:6.2f}%\n"
            )
        return text