class OpenPosition:
    def __init__(self, date, ticker, size, price):
        self.date = date
        self.ticker = ticker
        self.size = size
        self.price = price

    def __repr__(self):
        return f"OpenPosition(date={self.date}, ticker={self.ticker}, size={self.size}, price={self.price})"
    
    def as_csv(self):
        return f"{self.date},{self.ticker},{self.size},{self.price}"