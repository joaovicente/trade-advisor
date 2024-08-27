
from pydantic import BaseModel
from datetime import date

class TradeAction(BaseModel):
    date: date
    action: str
    ticker: str
    reason : str = None
    context : str = None

    def as_text(self, context=True, include_date=True):
        text = ""
        if include_date:
            text += f"{self.date} "
        text += f"{self.action} {self.ticker} because {self.reason}"
        if context and self.context and len(self.context) > 0 :
            text += "\nContext:\n"
            text += "\n".join(self.context)
        return text

    def __repr__(self):
        return f"TradeAction(date={self.date}, action={self.action}, ticker={self.ticker}, reason={self.reason}, context={self.context}"