from test.conftest import abspath
from types import SimpleNamespace

class FakeLine:
    def __init__(self, items):
        self._items = items
    
    def __getitem__(self, index):
        return self._items[index-1]
    
    def __setitem__(self, index, value):
        self._items[index-1] = value
    
    def __delitem__(self, index):
        del self._items[index-1]
    
    def __str__(self):
        return str(self._items)

class FakeStrategy:
    def __init__(self, name=None, rsi=[], rsi_ma=[], bb_bot=[], bb_mid=[], bb_top=[], params={}):
        self.params = SimpleNamespace(**params) # access dictionary values using dot notation
        self.rsi = { name: FakeLine(rsi)}
        self.rsi_ma = { name : FakeLine(rsi_ma)}
        self.b_band = { name : SimpleNamespace(
            lines=SimpleNamespace(
                bot=FakeLine(bb_bot), 
                mid=FakeLine(bb_mid), 
                top=FakeLine(bb_top))
            ) }
        
    def getposition(self, data):
        position = SimpleNamespace(price=data.position_price)
        return position
        
    def buy_upon_bb_bot_upwards_crossover_with_rsi_reenforcement(self, name, data):
        condition = data.close[-1] < self.b_band[name].lines.bot[-1] \
            and data.close[0] > self.b_band[name].lines.bot[0]\
            and self.rsi[name][0] < self.params.lower_rsi
        return condition
    
    def sell_upon_bb_mid_hat_inflection(self, name, data):
        condition = data.close[0] > self.getposition(data).price\
            and self.b_band[name].lines.mid[-3] < self.b_band[name].lines.mid[-2]\
            and self.b_band[name].lines.mid[-2] > self.b_band[name].lines.mid[-1]\
            and self.b_band[name].lines.mid[-1] > self.b_band[name].lines.mid[0]\
            and data.close[0] < data.close[-2]
        return condition

    def sell_upon_bb_low_crossover(self, name, data):
        # close below bb-bot and loss % below bb_low_crossover_loss_tolerance
        condition = data.close[0] < self.b_band[name].lines.bot[0] \
            and ((1-(data.close[0] / self.getposition(data).price))*100) > self.params.bb_low_crossover_loss_tolerance
        return condition
    
    def sell_if_percent_loss(self, name, data):
        condition = data.close[0] < self.getposition(data).price * (1-(self.params.loss_pct_threshold / 100))
        return condition
class FakeData:
    def __init__(self, close=[], position_price=0):
        self.close = FakeLine(close)
        self.position_price = position_price
    
    
        
        