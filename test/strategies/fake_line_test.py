from fake_strategy import * 

def test_fake_line():
    line = FakeLine([1, 2, 3])
    assert line[0] == 3
    assert line[-1] == 2
    assert line[-2] == 1