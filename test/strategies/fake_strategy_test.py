
from fake_strategy import * 

name = 'X'

def test_fake_line():
    st = FakeStrategy( name=name,
                        rsi = [1,2,3],
                        rsi_ma = [4,5,6],
                        bb_bot=[7,8,9],
                        bb_mid=[10,11,12],
                        bb_top=[13,14,15],
                        params = {'lower_rsi': 45}
                        )
    assert st.rsi[name][-2] == 1
    assert st.rsi[name][-1] == 2
    assert st.rsi[name][0] == 3
    assert st.rsi_ma[name][-2] == 4
    assert st.rsi_ma[name][-1] == 5
    assert st.rsi_ma[name][0] == 6
    assert st.b_band[name].lines.bot[-2] == 7
    assert st.b_band[name].lines.bot[-1] == 8
    assert st.b_band[name].lines.bot[0] == 9
    assert st.b_band[name].lines.mid[-2] == 10
    assert st.b_band[name].lines.mid[-1] == 11
    assert st.b_band[name].lines.mid[0] == 12
    assert st.b_band[name].lines.top[-2] == 13
    assert st.b_band[name].lines.top[-1] == 14
    assert st.b_band[name].lines.top[0] == 15
    assert st.params.lower_rsi == 45
    
def test_buy_upon_bb_bot_upwards_crossover_with_rsi_reenforcement():
    close =  [100, 90, 100]
    rsi =    [ 38, 38,  38]
    bb_bot = [ 95, 95,  95]
    params = {'lower_rsi': 40}
    data = FakeData(close = close)
    st = FakeStrategy(name=name, rsi=rsi, bb_bot=bb_bot, params=params)
    assert st.buy_upon_bb_bot_upwards_crossover_with_rsi_reenforcement(name, data) == True
    
def test_sell_upon_bb_mid_hat_inflection_and_close_above_position():
    scenario = "Sell when bb-mid hat AND latest close above position price"
    position_price = 80 
    close =  [90, 100, 90] # latest close above position price
    bb_mid = [90, 100, 90]
    data = FakeData(close=close, position_price=position_price)
    st = FakeStrategy(name=name, bb_mid=bb_mid)
    assert st.sell_upon_bb_mid_hat_inflection(name, data) == True, scenario
    
    scenario = "Sell when bb-mid hat AND close above position price even if latest bb-mid is not"
    position_price = 80 
    close =  [90, 100, 90] # latest close above position price
    bb_mid = [60, 70,  60] # latest bb-mid below position price
    data = FakeData(close=close, position_price=position_price)
    st = FakeStrategy(name=name, bb_mid=bb_mid)
    assert st.sell_upon_bb_mid_hat_inflection(name, data) == True, scenario
    
    scenario = "Don't sell when bb-mid hat AND close below position price"
    position_price = 102 
    close =  [ 90, 100,  90] # latest close below position price
    bb_mid = [ 95, 110,  95] # mid hat above position
    data = FakeData(close=close, position_price=position_price)
    st = FakeStrategy(name=name, bb_mid=bb_mid)
    assert st.sell_upon_bb_mid_hat_inflection(name, data) == False, scenario
    
    scenario = "Don't sell when bb-mid hat AND close below position price even if latest bb-mid is above"
    position_price = 100
    close =  [ 90, 100,  90] # latest close below position price
    bb_mid = [ 95, 103,  101] # mid hat above position price
    data = FakeData(close=close, position_price=position_price)
    st = FakeStrategy(name=name, bb_mid=bb_mid)
    assert st.sell_upon_bb_mid_hat_inflection(name, data) == False, scenario
    
def test_sell_upon_bb_low_crossover():
    # Refine sell_upon_bb_low_crossover
    # Allow for some initial loss 
    # - within n (try 20) days of position placement (maybe optional)
    # - if loss is within a percentage (try 5) tolerance
    # - after a few days of breach
    # Use AMZN, NFLX, UNH, BRK-B, JPM, PFE to fine tune
    # Ensure bearish PFE is not adversely affected by tuning
    assert False, "Refine sell_upon_bb_low_crossovers to allow for some initial loss within"
    # Given a bb_low_crossover in the last n days
    # When loss goes below loss_tolerance - try 5% first - Observed recoveries NFLX(1.5%) AMZN(2.1%) JPM(3.6%) BRK-B(3.7%))
    # Then sell 