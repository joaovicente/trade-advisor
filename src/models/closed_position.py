class ClosedPosition:
    def __init__(self, date, ticker, size, price, closed_date, closed_price):
        self.date = date
        self.ticker = ticker
        self.size = size
        self.price = price
        self.closed_date = closed_date
        self.closed_price = closed_price

    def __repr__(self):
        return f"ClosedPosition(date={self.date}, ticker={self.ticker}, size={self.size}, price={self.price}, closed_date={self.closed_date}, closed_price={self.closed_price})"
    
    def as_csv(self):
        return f"{self.date},{self.ticker},{self.size},{self.price},{self.closed_date},{self.closed_price}"