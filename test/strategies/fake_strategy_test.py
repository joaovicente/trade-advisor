
from fake_strategy import * 

def test_fake_line():
    name = 'X'
    st = FakeStrategy( name='X',
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
    name = 'X'
    data = FakeData(close = [100, 90, 100])
    st = FakeStrategy( name='X', 
                        rsi = [38, 38, 38],
                        bb_bot = [95, 95],
                        params = {'lower_rsi': 40}
                        )
    assert st.buy_upon_bb_bot_upwards_crossover_with_rsi_reenforcement(name, data) == True