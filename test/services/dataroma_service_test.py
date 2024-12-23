from services.dataroma_service import DataromaService

def test_dataroma_service():
    dataroma = DataromaService()
    assert dataroma.num_buys_by_ticker("MSFT") >= 0