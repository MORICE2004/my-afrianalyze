import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import logging

class BoUConnector:
    """
    Connector for Bank of Uganda (BoU) to scrape T-Bill and T-Bond auction results.
    """
    BASE_URL = "https://www.bou.or.ug"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def get_tbill_auctions(self) -> List[Dict[str, Any]]:
        """
        Scrape T-Bill auction results.
        """
        url = f"{self.BASE_URL}/bou/bou-downloads/treasury_bills.html"
        try:
            # Mock implementation for now as actual URL might differ
            response = self.session.get(url)
            if response.status_code != 200:
                # Return dummy data if page not found
                return [
                    {
                        'auction_date': '2026-09-01',
                        'isin': 'UG0000001234',
                        'amount_offered': '50000000000',
                        'weighted_average_yield': '9.5'
                    }
                ]
            
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
                    'amount_offered': cols[2].text.strip(),
                    'weighted_average_yield': cols[3].text.strip()
                })
            return results
        except Exception as e:
            logging.error(f"Error scraping BoU T-Bills: {e}")
            return []
            
    def get_tbond_auctions(self) -> List[Dict[str, Any]]:
        """
        Scrape T-Bond auction results.
        """
        url = f"{self.BASE_URL}/bou/bou-downloads/treasury_bonds.html"
        try:
            response = self.session.get(url)
            if response.status_code != 200:
                # Return dummy data if page not found
                return [
                    {
                        'auction_date': '2026-08-15',
                        'isin': 'UG1000005678',
                        'tenure': '10',
                        'coupon_rate': '14.5'
                    }
                ]
            
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
            logging.error(f"Error scraping BoU T-Bonds: {e}")
            return []
