import iso4217


class ClosedPosition:
    def __init__(self, date, ticker, size, price, currency, closed_date, closed_price, commission=0.00):
        self.date = date
        self.ticker = ticker
        self.size = size
        self.price = price
        if currency not in [c.code for c in iso4217.Currency]:
            raise ValueError(f"Invalid currency: {currency}") 
        self.currency = currency
        self.closed_date = closed_date
        self.closed_price = closed_price
        self.commission = commission

    def __repr__(self):
        return f"ClosedPosition(date={self.date}, ticker={self.ticker}, size={self.size}, price={self.price}, currency={self.currency} closed_date={self.closed_date}, closed_price={self.closed_price}, commission={self.commission} )"
    
    def as_csv(self):
        return f"{self.date},{self.ticker},{self.size},{self.price},{self.currency},{self.closed_date},{self.closed_price},{self.commission}"