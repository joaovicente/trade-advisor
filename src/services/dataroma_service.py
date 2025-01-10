
from bs4 import BeautifulSoup
import pandas as pd
import requests

class DataromaService:
    def __init__(self):
        self.symbol_quarter_buys_dict = self.web_scrape(url="https://www.dataroma.com/m/g/portfolio_b.php?q=q&o=c", 
                               num_columns=9, column_label="Buys▼")
        self.symbol_6months_buys_dict = self.web_scrape(url="https://www.dataroma.com/m/g/portfolio_b.php?q=h&o=c", 
                               num_columns=9, column_label="Buys▼")
        self.symbol_ownership_dict = self.web_scrape(url="https://www.dataroma.com/m/g/portfolio.php?pct=0&o=c", 
                               num_columns=10, column_label="Ownershipcount▼")

    def num_quarter_buys_by_ticker(self, ticker):
        # Dataroma uses '.' (e.g. BRK.B) notation instead of '-' (BRK-B)
        ticker = ticker.replace('-', '.')
        if ticker in self.symbol_quarter_buys_dict:
            return int(self.symbol_quarter_buys_dict[ticker])
        else:
            return 0
        
    def num_6month_buys_by_ticker(self, ticker):
        # Dataroma uses '.' (e.g. BRK.B) notation instead of '-' (BRK-B)
        ticker = ticker.replace('-', '.')
        if ticker in self.symbol_6months_buys_dict:
            return int(self.symbol_6months_buys_dict[ticker])
        else:
            return 0
        
    def num_owners_by_ticker(self, ticker):
        ticker = ticker.replace('-', '.')
        if ticker in self.symbol_ownership_dict:
            return int(self.symbol_ownership_dict[ticker])
        else:
            return 0

    def web_scrape(self, url, num_columns, column_label):
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
            headers = [header.get_text(strip=True) for header in table.find_all("td")][:num_columns]
            # Extract rows
            rows = []
            for row in table.find("tbody").find_all("tr"):
                cells = [cell.get_text(strip=True) for cell in row.find_all("td")]
                rows.append(cells)
            # Create a DataFrame
            df = pd.DataFrame(rows, columns=headers)
            #print(df)
            # Create Symbol to value dictionary
            return df.set_index('Symbol')[column_label].to_dict()
        else:
            return {}