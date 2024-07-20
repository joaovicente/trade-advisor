
class TradeAction:
    def __init__(self, date, action, ticker, reason=None, context=None):
        self.date = date
        self.action = action
        self.ticker = ticker
        self.reason = reason
        self.context = context

    def __repr__(self):
        return f"TradeAction(date={self.date}, action={self.action}, ticker={self.ticker}, reason={self.reason}, context={self.context}"