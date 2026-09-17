import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import logging

class BoTConnector:
    """
    Connector for Bank of Tanzania (BoT) to scrape T-Bill and T-Bond auction results.
    """
    BASE_URL = "https://www.bot.go.tz"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def get_tbill_auctions(self) -> List[Dict[str, Any]]:
        """
        Scrape T-Bill auction results.
        """
        url = f"{self.BASE_URL}/FinancialMarkets/TBillAuctions"
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            table = soup.find('table')
            if not table:
                return results
                
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all(['td', 'th'])
                # Skip header rows that are purely headers or merged headers
                if any(c.name == 'th' for c in cols) or len(cols) < 4:
                    continue
                # Extract assuming standard structure once data rows are hit
                results.append({
                    'auction_date': cols[0].text.strip(),
                    'isin': cols[1].text.strip(),
                    'amount_offered': cols[2].text.strip(),
                    'weighted_average_yield': cols[3].text.strip()
                })
            return results
        except Exception as e:
            logging.error(f"Error scraping BoT T-Bills: {e}")
            return []
            
    def get_tbond_auctions(self) -> List[Dict[str, Any]]:
        """
        Scrape T-Bond auction results.
        """
        url = f"{self.BASE_URL}/FinancialMarkets/TBondAuctions"
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            table = soup.find('table')
            if not table:
                return results
                
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all(['td', 'th'])
                if any(c.name == 'th' for c in cols) or len(cols) < 4:
                    continue
                results.append({
                    'auction_date': cols[0].text.strip(),
                    'isin': cols[1].text.strip(),
                    'tenure': cols[2].text.strip(),
                    'coupon_rate': cols[3].text.strip()
                })
            return results
        except Exception as e:
            logging.error(f"Error scraping BoT T-Bonds: {e}")
            return []
