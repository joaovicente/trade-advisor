class SelectedTickers:
    def __init__(self, ticker):
        self.ticker = ticker

    def __repr__(self):
        return f"Ticker(ticker={self.ticker})"