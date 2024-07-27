
from pydantic import BaseModel
from datetime import date

class TradeAction(BaseModel):
    date: date
    action: str
    ticker: str
    reason : str = None
    context : str = None

    def as_text(self):
        text = f"{self.date} {self.action} {self.ticker} because {self.reason}\n"
        if self.context:
            text += "Context:\n"
            text += "\n".join(self.context)
        return text

    def __repr__(self):
        return f"TradeAction(date={self.date}, action={self.action}, ticker={self.ticker}, reason={self.reason}, context={self.context}"