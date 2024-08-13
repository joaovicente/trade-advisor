
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
    
def test_dont_sell_upon_bb_mid_hat_inflection_and_close_above_position_only_when_bull():
    scenario = "Don't sell when bb-mid hat AND close below position price"
    position_price = 102 
    close =  [ 100, 100, 100, 100] # latest close below position price
    bb_mid = [ 95, 110,  95, 92] # mid hat above position
    data = FakeData(close=close, position_price=position_price)
    st = FakeStrategy(name=name, bb_mid=bb_mid)
    assert st.sell_upon_bb_mid_hat_inflection(name, data) == False, scenario
    
def test_sell_upon_bb_mid_hat_inflection_and_close_above_position_only_when_bull():
    scenario = "Sell when bb-mid hat AND close below position price"
    position_price = 80 
    close =  [ 100, 100, 100, 100] # latest close below position price
    bb_mid = [ 95, 110,  95, 92] # mid hat above position
    data = FakeData(close=close, position_price=position_price)
    st = FakeStrategy(name=name, bb_mid=bb_mid)
    assert st.sell_upon_bb_mid_hat_inflection(name, data) == True, scenario
    
def test_dont_sell_upon_bb_mid_hat_inflection_rebound_tolerance_amzn():
    #2023-09-27, AMZN BUY CREATE, 125.98
    #2023-09-27 BUY AMZN because AMZN Close (125.98,125.98) crossover Bollinger bottom (125.47) while RSI (34.51) below 35.00
    #2023-09-28, AMZN BUY EXECUTED, Price: 124.04, Cost: 2953.80, Comm 0.00
    #2023-12-29, AMZN, close:  151.94,  rsi: 59.01, rsi-ma: 61.52, bb-top: 156.49, bb-mid: 149.82, bb-bot: 143.16, position: 124.04, pnl-pct: 18.36%
    #2024-01-02, AMZN, close:  149.93,  rsi: 52.89, rsi-ma: 60.91, bb-top: 156.51, bb-mid: 149.97, bb-bot: 143.43, position: 124.04, pnl-pct: 17.27%
    #2024-01-03, AMZN, close:  148.47,  rsi: 48.92, rsi-ma: 60.05, bb-top: 156.30, bb-mid: 150.15, bb-bot: 144.00, position: 124.04, pnl-pct: 16.45%
    #2024-01-04, AMZN, close:  144.57,  rsi: 40.23, rsi-ma: 58.63, bb-top: 156.51, bb-mid: 150.03, bb-bot: 143.56, position: 124.04, pnl-pct: 14.20%
    #2024-01-04 SELL AMZN because AMZN Bollinger mid inflection (149.82, 149.97, 150.15, 150.03)
    #2024-01-05, AMZN SELL EXECUTED, Price: 144.69, Cost: 2953.80, Comm 0.00
    #2024-01-05, AMZN OPERATION PROFIT, GROSS 491.74, NET 491.74
    #2024-01-05, AMZN, close:  145.24,  rsi: 42.13, rsi-ma: 57.46, bb-top: 156.42, bb-mid: 150.07, bb-bot: 143.72, position: 0.00, pnl-pct: 0.00%
    #2024-01-08, AMZN, close:  149.10,  rsi: 51.67, rsi-ma: 57.04, bb-top: 156.38, bb-mid: 150.18, bb-bot: 143.98, position: 0.00, pnl-pct: 0.00%
    scenario = "Don't sell when bb-mid hat with immediate bb-mid rebound AMZN"
    position_price = 128.98
    close =  [149.93, 148.47, 144.57, 145.24] 
    bb_mid = [149.97, 150.15, 150.03, 150.07] # Rebound on last entry
    data = FakeData(close=close, position_price=position_price)
    st = FakeStrategy(name=name, bb_mid=bb_mid)
    assert st.sell_upon_bb_mid_hat_inflection(name, data) == False, scenario

def test_dont_sell_upon_bb_mid_hat_inflection_rebound_tolerance_crm():
    #2023-09-27, CRM BUY CREATE, 202.73
    #2023-09-27 BUY CRM because CRM Close (202.49,202.73) crossover Bollinger bottom (201.88) while RSI (31.95) below 35.00
    #2023-09-28, CRM BUY EXECUTED, Price: 200.76, Cost: 2970.85, Comm 0.00
    #2023-12-22, CRM, close:  266.34,  rsi: 74.76, rsi-ma: 72.10, bb-top: 276.88, bb-mid: 252.44, bb-bot: 228.01, position: 200.76, pnl-pct: 24.62%
    #2023-12-26, CRM, close:  266.22,  rsi: 74.53, rsi-ma: 72.27, bb-top: 276.08, bb-mid: 254.52, bb-bot: 232.95, position: 200.76, pnl-pct: 24.59%
    #2023-12-27, CRM, close:  266.72,  rsi: 74.87, rsi-ma: 72.46, bb-top: 273.98, bb-mid: 256.61, bb-bot: 239.23, position: 200.76, pnl-pct: 24.73%
    #2023-12-28, CRM, close:  265.58,  rsi: 72.47, rsi-ma: 72.46, bb-top: 271.32, bb-mid: 258.37, bb-bot: 245.41, position: 200.76, pnl-pct: 24.41%
    #2023-12-29, CRM, close:  263.14,  rsi: 67.49, rsi-ma: 72.10, bb-top: 271.69, bb-mid: 258.93, bb-bot: 246.17, position: 200.76, pnl-pct: 23.71%
    #2024-01-02, CRM, close:  256.13,  rsi: 55.65, rsi-ma: 70.93, bb-top: 271.54, bb-mid: 258.74, bb-bot: 245.93, position: 200.76, pnl-pct: 21.62%
    #2024-01-02, CRM SELL CREATE, 256.13
    #2024-01-02 SELL CRM because CRM Bollinger mid inflection (256.61, 258.37, 258.93, 258.74)
    #2024-01-03, CRM SELL EXECUTED, Price: 253.50, Cost: 2970.85, Comm 0.00
    #2024-01-03, CRM OPERATION PROFIT, GROSS 780.45, NET 780.45
    #2024-01-03, CRM, close:  251.84,  rsi: 49.88, rsi-ma: 69.42, bb-top: 271.46, bb-mid: 258.79, bb-bot: 246.13, position: 0.00, pnl-pct: 0.00%
    #2024-01-04, CRM, close:  251.24,  rsi: 49.11, rsi-ma: 67.97, bb-top: 271.44, bb-mid: 258.81, bb-bot: 246.17, position: 0.00, pnl-pct: 0.00%
    #2024-01-05, CRM, close:  251.12,  rsi: 48.95, rsi-ma: 66.61, bb-top: 271.27, bb-mid: 258.91, bb-bot: 246.54, position: 0.00, pnl-pct: 0.00%
    #2024-01-08, CRM, close:  260.87,  rsi: 60.39, rsi-ma: 66.17, bb-top: 270.99, bb-mid: 259.51, bb-bot: 248.02, position: 0.00, pnl-pct: 0.00%
    #2024-01-09, CRM, close:  261.34,  rsi: 60.84, rsi-ma: 65.79, bb-top: 270.82, bb-mid: 260.03, bb-bot: 249.25, position: 0.00, pnl-pct: 0.00%
    #2024-01-10, CRM, close:  264.13,  rsi: 63.52, rsi-ma: 65.63, bb-top: 270.91, bb-mid: 260.63, bb-bot: 250.36, position: 0.00, pnl-pct: 0.00%     
    scenario = "Don't sell when bb-mid hat with immediate bb-mid rebound AMZN"
    position_price = 202.73
    close =  [265.58, 263.14, 263.13, 251.84] 
    bb_mid = [258.37, 258.93, 258.74, 258.79] # Rebound on last entry
    data = FakeData(close=close, position_price=position_price)
    st = FakeStrategy(name=name, bb_mid=bb_mid)
    assert st.sell_upon_bb_mid_hat_inflection(name, data) == False, scenario
    
def test_dont_sell_upon_bb_mid_hat_inflection_rebound_tolerance_nflx():
    # Don't sell when close recovery is shown in the second bb-mid decay
    #2023-10-16, NFLX BUY CREATE, 360.82
    #2023-10-16 BUY NFLX because NFLX Close (355.68,360.82) crossover Bollinger bottom (357.62) while RSI (33.25) below 35.00
    #2023-10-17, NFLX BUY EXECUTED, Price: 361.10, Cost: 3002.33, Comm 0.00
    #2024-01-17, NFLX, close:  480.33,  rsi: 52.03, rsi-ma: 58.25, bb-top: 499.81, bb-mid: 484.40, bb-bot: 469.00, position: 361.10, pnl-pct: 24.82%
    #2024-01-18, NFLX, close:  485.31,  rsi: 55.09, rsi-ma: 58.02, bb-top: 499.75, bb-mid: 484.36, bb-bot: 468.97, position: 361.10, pnl-pct: 25.59%
    #2024-01-19, NFLX, close:  482.95,  rsi: 53.35, rsi-ma: 57.69, bb-top: 498.35, bb-mid: 483.76, bb-bot: 469.16, position: 361.10, pnl-pct: 25.23%
    #2024-01-19, NFLX SELL CREATE, 482.95
    #2024-01-19 SELL NFLX because NFLX Bollinger mid inflection sustained (483.99, 484.40, 484.36, 483.76)
    #2024-01-22, NFLX SELL EXECUTED, Price: 487.55, Cost: 3002.33, Comm 0.00
    #2024-01-22, NFLX OPERATION PROFIT, GROSS 1051.36, NET 1051.36
    #2024-01-22, NFLX, close:  485.71,  rsi: 55.14, rsi-ma: 57.51, bb-top: 497.99, bb-mid: 483.58, bb-bot: 469.17, position: 0.00, pnl-pct: 0.00%
    scenario = "Don't sell when bb-mid hat consecutive lower bb-mid if close is recovering"
    position_price = 360.82
    close =  [480.33, 485.31, 482.95, 485.71] 
    bb_mid = [483.99, 484.40, 484.36, 483.76] 
    data = FakeData(close=close, position_price=position_price)
    st = FakeStrategy(name=name, bb_mid=bb_mid)
    assert st.sell_upon_bb_mid_hat_inflection(name, data) == False, scenario
    
def test_dont_sell_upon_bb_mid_hat_inflection_rebound_tolerance_msft():
    #TODO: Find a way to be more tolerant when there are oscillations, but loss is below 3%
    #2023-09-27, MSFT BUY CREATE, 312.79
    #2023-09-27 BUY MSFT because MSFT Close (312.14,312.79) crossover Bollinger bottom (311.73) while RSI (34.73) below 35.00
    #2023-09-28, MSFT BUY EXECUTED, Price: 310.99, Cost: 2982.74, Comm 0.00 
    #2023-12-08, MSFT, close:  374.23,  rsi: 58.26, rsi-ma: 62.46, bb-top: 382.50, bb-mid: 373.87, bb-bot: 365.23, position: 310.99, pnl-pct: 16.90%
    #2023-12-11, MSFT, close:  371.30,  rsi: 54.89, rsi-ma: 61.92, bb-top: 382.45, bb-mid: 373.95, bb-bot: 365.44, position: 310.99, pnl-pct: 16.24%
    #2023-12-12, MSFT, close:  374.38,  rsi: 57.66, rsi-ma: 61.62, bb-top: 382.16, bb-mid: 374.33, bb-bot: 366.51, position: 310.99, pnl-pct: 16.93%
    #2023-12-13, MSFT, close:  374.37,  rsi: 57.65, rsi-ma: 61.33, bb-top: 382.14, bb-mid: 374.54, bb-bot: 366.94, position: 310.99, pnl-pct: 16.93%
    #2023-12-14, MSFT, close:  365.93,  rsi: 48.24, rsi-ma: 60.40, bb-top: 382.58, bb-mid: 374.35, bb-bot: 366.12, position: 310.99, pnl-pct: 15.01%
    #2023-12-14, MSFT SELL CREATE, 365.93
    #2023-12-14 SELL MSFT because MSFT Bollinger mid inflection (373.95, 374.33, 374.54, 374.35)
    #2023-12-15, MSFT SELL EXECUTED, Price: 366.85, Cost: 2982.74, Comm 0.00
    #2023-12-15, MSFT OPERATION PROFIT, GROSS 535.76, NET 535.76
    #2023-12-15, MSFT, close:  370.73,  rsi: 52.94, rsi-ma: 59.86, bb-top: 382.41, bb-mid: 374.08, bb-bot: 365.75, position: 0.00, pnl-pct: 0.00%
    #2023-12-18, MSFT, close:  372.65,  rsi: 54.72, rsi-ma: 59.50, bb-top: 382.35, bb-mid: 374.22, bb-bot: 366.09, position: 0.00, pnl-pct: 0.00%
    #2023-12-19, MSFT, close:  373.26,  rsi: 55.29, rsi-ma: 59.20, bb-top: 382.01, bb-mid: 374.01, bb-bot: 366.01, position: 0.00, pnl-pct: 0.00%
    #2023-12-20, MSFT, close:  370.62,  rsi: 52.20, rsi-ma: 58.70, bb-top: 382.02, bb-mid: 373.89, bb-bot: 365.76, position: 0.00, pnl-pct: 0.00%
    #2023-12-21, MSFT, close:  373.54,  rsi: 55.19, rsi-ma: 58.45, bb-top: 381.60, bb-mid: 373.67, bb-bot: 365.75, position: 0.00, pnl-pct: 0.00%
    #2023-12-22, MSFT, close:  374.58,  rsi: 56.24, rsi-ma: 58.29, bb-top: 381.28, bb-mid: 373.53, bb-bot: 365.78, position: 0.00, pnl-pct: 0.00%
    pass

def test_sell_upon_bb_low_crossover():
    scenario = "Sell if day after bb-bot downwards crossover loss above 5%"
    position_price = 100
    close =  [ 101,  94] # latest close at 6 % loss 
    bb_bot = [ 100, 100] 
    params = {'bb_low_crossover_loss_tolerance': 5, 'bb_low_crossover_days_watch': 0}
    data = FakeData(close=close, position_price=position_price)
    st = FakeStrategy(name=name, bb_bot=bb_bot, params=params)
    assert st.sell_upon_bb_low_crossover(name, data) == True, scenario
    
    scenario = "Don't sell if day after bb-bot downwards crossover loss below 5%"
    position_price = 100
    close =  [ 101,  96] # latest close at 4 % loss 
    bb_bot = [ 100, 100] 
    params = {'bb_low_crossover_loss_tolerance': 5, 'bb_low_crossover_days_watch': 0}
    data = FakeData(close=close, position_price=position_price)
    st = FakeStrategy(name=name, bb_bot=bb_bot, params=params)
    assert st.sell_upon_bb_low_crossover(name, data) == False, scenario
    
    