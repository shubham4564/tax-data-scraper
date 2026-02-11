"""
State Tax Code Scraper

Handles scraping tax codes from state revenue department websites.
Each state has different structure - this provides a framework with
specific implementations for major states.
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# State tax website configurations
STATE_CONFIGS = {
    'california': {
        'name': 'California',
        'revenue_code_url': 'https://leginfo.legislature.ca.gov/faces/codes.xhtml',
        'tax_codes': ['RTC'],  # Revenue and Taxation Code
        'scraper_class': 'CaliforniaScraper'
    },
    'new_york': {
        'name': 'New York',
        'base_url': 'https://www.nysenate.gov/legislation/laws/TAX',
        'scraper_class': 'NewYorkScraper'
    },
    'texas': {
        'name': 'Texas',
        'base_url': 'https://statutes.capitol.texas.gov',
        'tax_codes': ['TX'],  # Tax Code
        'scraper_class': 'TexasScraper'
    },
    'florida': {
        'name': 'Florida',
        'base_url': 'http://www.leg.state.fl.us/statutes/',
        'chapters': ['212', '220'],  # Sales tax, Corporate income tax
        'scraper_class': 'FloridaScraper'
    },
    'illinois': {
        'name': 'Illinois',
        'base_url': 'https://www.ilga.gov/legislation/ilcs/ilcs.asp',
        'scraper_class': 'IllinoisScraper'
    }
}


class BaseStateScraper:
    """Base class for state tax code scrapers"""
    
    def __init__(self, state_config: Dict, rate_limit: float = 1.5):
        self.config = state_config
        self.state_name = state_config['name']
        self.rate_limit = rate_limit
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Research/Educational Tax IR System)'
        })
        self.output_dir = Path(f"data/raw/states/{state_config['name'].lower().replace(' ', '_')}")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def scrape(self) -> List[Dict]:
        """Override in subclass"""
        raise NotImplementedError
    
    def _save_section(self, section_data: Dict, filename: str):
        """Save section to file"""
        filepath = self.output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(section_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved {filename}")


class CaliforniaScraper(BaseStateScraper):
    """Scraper for California Revenue and Taxation Code"""
    
    def scrape(self, max_sections: Optional[int] = None) -> List[Dict]:
        """
        Scrape California Revenue and Taxation Code
        
        MANUAL STEP: California's legislative site requires interactive navigation.
        Alternative: Download PDFs from https://www.ftb.ca.gov/tax-pros/law/
        """
        logger.info("Starting California tax code scraping...")
        
        # California's site structure makes automated scraping difficult
        # Provide manual download instructions
        
        manual_instructions = {
            'state': 'California',
            'instruction': 'MANUAL DOWNLOAD REQUIRED',
            'steps': [
                '1. Go to https://www.ftb.ca.gov/tax-pros/law/',
                '2. Download "Revenue and Taxation Code" sections',
                '3. Alternative: https://leginfo.legislature.ca.gov/faces/codes.xhtml',
                '4. Select "Revenue and Taxation Code"',
                '5. Download individual divisions/chapters as needed',
                '6. Save PDFs to: ' + str(self.output_dir)
            ],
            'key_sections': [
                'Division 2: Other Taxes (Sales, Use Tax)',
                'Part 10: Personal Income Tax',
                'Part 11: Corporation Tax Law'
            ]
        }
        
        with open(self.output_dir / 'MANUAL_DOWNLOAD_INSTRUCTIONS.json', 'w') as f:
            json.dump(manual_instructions, f, indent=2)
        
        logger.warning("California requires manual download. See MANUAL_DOWNLOAD_INSTRUCTIONS.json")
        return []


class NewYorkScraper(BaseStateScraper):
    """Scraper for New York Tax Law"""
    
    def scrape(self, max_sections: Optional[int] = None) -> List[Dict]:
        logger.info("Starting New York tax law scraping...")
        
        try:
            time.sleep(self.rate_limit)
            response = self.session.get(self.config['base_url'])
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            sections = []
            
            # Find article links
            for link in soup.find_all('a', href=re.compile(r'/legislation/laws/TAX/\w+')):
                section_id = link['href'].split('/')[-1]
                sections.append({
                    'section_id': section_id,
                    'title': link.get_text(strip=True),
                    'url': f"https://www.nysenate.gov{link['href']}"
                })
                
                if max_sections and len(sections) >= max_sections:
                    break
            
            # Scrape each section
            all_data = []
            for section in sections:
                section_data = self._scrape_ny_section(section)
                if section_data:
                    all_data.append(section_data)
                    self._save_section(section_data, f"section_{section['section_id']}.json")
            
            return all_data
            
        except Exception as e:
            logger.error(f"Error scraping New York: {e}")
            return []
    
    def _scrape_ny_section(self, section: Dict) -> Optional[Dict]:
        """Scrape individual NY Tax Law section"""
        try:
            time.sleep(self.rate_limit)
            response = self.session.get(section['url'])
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract content
            content_div = soup.find('div', class_='law-section-content') or soup.find('article')
            if not content_div:
                return None
            
            return {
                'state': 'New York',
                'section_id': section['section_id'],
                'title': section['title'],
                'text': content_div.get_text(strip=True),
                'url': section['url'],
                'scraped_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error scraping NY section {section['section_id']}: {e}")
            return None


class TexasScraper(BaseStateScraper):
    """Scraper for Texas Tax Code"""
    
    def scrape(self, max_sections: Optional[int] = None) -> List[Dict]:
        logger.info("Starting Texas tax code scraping...")
        
        base_url = "https://statutes.capitol.texas.gov"
        toc_url = f"{base_url}/Docs/TX/htm/TX.htm"
        
        try:
            time.sleep(self.rate_limit)
            response = self.session.get(toc_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            chapters = []
            
            # Find chapter links
            for link in soup.find_all('a', href=re.compile(r'TX\.\d+\.htm')):
                chapter_num = re.search(r'TX\.(\d+)', link['href']).group(1)
                chapters.append({
                    'chapter': chapter_num,
                    'title': link.get_text(strip=True),
                    'url': f"{base_url}/Docs/TX/htm/{link['href']}"
                })
            
            # Scrape chapters
            all_data = []
            for chapter in chapters[:max_sections] if max_sections else chapters:
                chapter_data = self._scrape_tx_chapter(chapter)
                if chapter_data:
                    all_data.append(chapter_data)
                    self._save_section(chapter_data, f"chapter_{chapter['chapter']}.json")
            
            return all_data
            
        except Exception as e:
            logger.error(f"Error scraping Texas: {e}")
            return []
    
    def _scrape_tx_chapter(self, chapter: Dict) -> Optional[Dict]:
        """Scrape Texas Tax Code chapter"""
        try:
            time.sleep(self.rate_limit)
            response = self.session.get(chapter['url'])
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract sections
            sections = []
            for section_div in soup.find_all('div', class_='section'):
                sections.append({
                    'text': section_div.get_text(strip=True)
                })
            
            return {
                'state': 'Texas',
                'chapter': chapter['chapter'],
                'title': chapter['title'],
                'sections': sections,
                'url': chapter['url'],
                'scraped_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error scraping TX chapter {chapter['chapter']}: {e}")
            return None


class FloridaScraper(BaseStateScraper):
    """Scraper for Florida Statutes (tax chapters)"""
    
    def scrape(self, max_sections: Optional[int] = None) -> List[Dict]:
        logger.info("Starting Florida statutes scraping...")
        
        # Key tax chapters
        chapters = self.config.get('chapters', ['212', '220'])
        
        all_data = []
        for chapter in chapters:
            chapter_url = f"{self.config['base_url']}/index.cfm?App_mode=Display_Statute&Title_Request=true&Title_Number={chapter}"
            
            chapter_data = self._scrape_fl_chapter(chapter, chapter_url)
            if chapter_data:
                all_data.append(chapter_data)
                self._save_section(chapter_data, f"chapter_{chapter}.json")
        
        return all_data
    
    def _scrape_fl_chapter(self, chapter: str, url: str) -> Optional[Dict]:
        """Scrape Florida statute chapter"""
        try:
            time.sleep(self.rate_limit)
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Florida's structure varies - basic text extraction
            content = soup.find('div', class_='statute') or soup.find('body')
            
            return {
                'state': 'Florida',
                'chapter': chapter,
                'text': content.get_text(strip=True) if content else '',
                'url': url,
                'scraped_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error scraping FL chapter {chapter}: {e}")
            return None


class StateTaxScraperManager:
    """Manages scraping across multiple states"""
    
    def __init__(self):
        self.scrapers = {
            'california': CaliforniaScraper,
            'new_york': NewYorkScraper,
            'texas': TexasScraper,
            'florida': FloridaScraper
        }
    
    def scrape_state(self, state_key: str, max_sections: Optional[int] = None) -> List[Dict]:
        """Scrape a specific state's tax code"""
        if state_key not in STATE_CONFIGS:
            logger.error(f"Unknown state: {state_key}")
            return []
        
        config = STATE_CONFIGS[state_key]
        scraper_class = self.scrapers.get(state_key)
        
        if not scraper_class:
            logger.warning(f"No scraper implemented for {state_key}")
            return []
        
        scraper = scraper_class(config)
        return scraper.scrape(max_sections=max_sections)
    
    def scrape_all_states(self, max_sections_per_state: Optional[int] = None):
        """Scrape all configured states"""
        results = {}
        
        for state_key in self.scrapers.keys():
            logger.info(f"\n{'='*60}\nScraping {state_key.upper()}\n{'='*60}")
            results[state_key] = self.scrape_state(state_key, max_sections_per_state)
            time.sleep(2)  # Extra delay between states
        
        # Save summary
        summary = {
            'states_scraped': list(results.keys()),
            'total_sections': sum(len(v) for v in results.values()),
            'scraped_date': datetime.now().isoformat()
        }
        
        with open('data/raw/states/scraping_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        return results


def main():
    """Main execution"""
    print("=" * 60)
    print("State Tax Code Scraper")
    print("=" * 60)
    print()
    print("Available states:")
    for i, (key, config) in enumerate(STATE_CONFIGS.items(), 1):
        print(f"{i}. {config['name']}")
    print()
    print("IMPORTANT NOTES:")
    print("- Some states require manual download (will create instructions)")
    print("- Rate limiting: 1.5 seconds between requests")
    print("- Check robots.txt compliance for each state")
    print()
    
    manager = StateTaxScraperManager()
    
    choice = input("Scrape:\n1. All states\n2. Specific state\n3. Test mode (5 sections per state)\nChoice: ")
    
    if choice == '1':
        manager.scrape_all_states()
    elif choice == '2':
        state = input("Enter state key (california, new_york, texas, florida): ").lower()
        manager.scrape_state(state)
    elif choice == '3':
        manager.scrape_all_states(max_sections_per_state=5)
    
    print("\nScraping complete! Check data/raw/states/ for output.")


if __name__ == "__main__":
    main()
