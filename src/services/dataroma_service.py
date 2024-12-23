
from bs4 import BeautifulSoup
import pandas as pd
import requests

class DataromaService:
    def __init__(self):
        self.symbol_buys_dict = {}
        self.load_quarter_buys()

    def num_buys_by_ticker(self, ticker):
        if ticker in self.symbol_buys_dict:
            return int(self.symbol_buys_dict[ticker])
        else:
            return 0

    def load_quarter_buys(self):
        # Dataroma quarter buys URL
        url = "https://www.dataroma.com/m/g/portfolio_b.php?q=q"

        # Custom headers
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }

        # Make the request
        response = requests.get(url, headers=headers)

        # Check for successful response
        if response.status_code == 200:
            html_content = response.text
            
            # Parse the HTML
            soup = BeautifulSoup(html_content, "html.parser")
            table = soup.find("table", {"id": "grid"})
            
            # Extract headers
            headers = [header.get_text(strip=True) for header in table.find_all("td")][:9]

            # Extract rows
            rows = []
            for row in table.find("tbody").find_all("tr"):
                cells = [cell.get_text(strip=True) for cell in row.find_all("td")]
                rows.append(cells)

            # Create a DataFrame
            df = pd.DataFrame(rows, columns=headers)

            # Create Symbol to (number of) Buys dictionary
            self.symbol_buys_dict = df.set_index('Symbol')['Buys'].to_dict()