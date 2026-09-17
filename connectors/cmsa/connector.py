import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import logging

class CMSAConnector:
    """
    Connector for Capital Markets and Securities Authority (CMSA) 
    to scrape licensed fund managers and related market info.
    """
    BASE_URL = "https://www.cmsa.go.tz"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def get_licensed_fund_managers(self) -> List[Dict[str, str]]:
        """
        Scrape licensed fund managers from CMSA website.
        """
        url = f"{self.BASE_URL}/licensees/fund-managers"
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            managers = []
            
            table = soup.find('table')
            if not table:
                return managers
                
            for row in table.find_all('tr')[1:]:
                cols = row.find_all('td')
                if len(cols) >= 2:
                    managers.append({
                        'name': cols[0].text.strip(),
                        'license_number': cols[1].text.strip()
                    })
            return managers
        except Exception as e:
            logging.error(f"Error scraping CMSA Fund Managers: {e}")
            return []
