
class TradeAction:
    def __init__(self, date, action, ticker, reason=None, context=None):
        self.date = date
        self.action = action
        self.ticker = ticker
        self.reason = reason
        self.context = context

    def as_text(self):
        text = f"{self.date} {self.action} {self.ticker} because {self.reason}\n"
        if self.context:
            text += "Context:\n"
            text += "\n".join(self.context)
        return text

    def __repr__(self):
        return f"TradeAction(date={self.date}, action={self.action}, ticker={self.ticker}, reason={self.reason}, context={self.context}"