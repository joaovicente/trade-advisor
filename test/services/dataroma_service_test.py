from services.dataroma_service import DataromaService

def test_dataroma_service():
    dataroma = DataromaService()
    assert len(dataroma.symbol_6months_buys_dict) > 0
    assert len(dataroma.symbol_ownership_dict) > 0
    assert len(dataroma.symbol_quarter_buys_dict) > 0