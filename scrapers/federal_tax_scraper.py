"""
Federal Tax Code Scraper - IRS Title 26 USC

Scrapes the Internal Revenue Code from Cornell LII and IRS.gov
Handles sections, subsections, amendments, and effective dates
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FederalTaxScraper:
    """Scrape federal tax code (26 USC) from Cornell Legal Information Institute"""
    
    BASE_URL = "https://www.law.cornell.edu/uscode/text/26"
    OUTPUT_DIR = Path("data/raw/federal/usc_title26")
    
    def __init__(self, rate_limit: float = 1.0):
        """
        Args:
            rate_limit: Seconds to wait between requests (be respectful)
        """
        self.rate_limit = rate_limit
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Research/Educational Tax IR System)'
        })
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
    def get_chapter_list(self) -> List[Dict[str, str]]:
        """Get list of all chapters in Title 26"""
        logger.info("Fetching chapter list...")
        response = self.session.get(self.BASE_URL)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        chapters = []
        
        # Find all chapter links
        for link in soup.find_all('a', href=re.compile(r'/uscode/text/26/chapter-\d+')):
            chapter_num = re.search(r'chapter-(\d+)', link['href']).group(1)
            chapters.append({
                'number': chapter_num,
                'title': link.get_text(strip=True),
                'url': f"{self.BASE_URL}/chapter-{chapter_num}"
            })
        
        logger.info(f"Found {len(chapters)} chapters")
        return chapters
    
    def get_sections_in_chapter(self, chapter_url: str) -> List[Dict[str, str]]:
        """Get all section URLs in a chapter"""
        time.sleep(self.rate_limit)
        response = self.session.get(chapter_url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        sections = []
        
        # Find section links
        for link in soup.find_all('a', href=re.compile(r'/uscode/text/26/\d+')):
            section_num = re.search(r'/26/(\d+[A-Z]?)', link['href'])
            if section_num:
                sections.append({
                    'number': section_num.group(1),
                    'title': link.get_text(strip=True),
                    'url': f"https://www.law.cornell.edu{link['href']}"
                })
        
        return sections
    
    def scrape_section(self, section_url: str, section_num: str) -> Dict:
        """Scrape a single IRC section with full text and metadata"""
        time.sleep(self.rate_limit)
        logger.info(f"Scraping section {section_num}...")
        
        try:
            response = self.session.get(section_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract section title
            title_elem = soup.find('h2') or soup.find('h1')
            title = title_elem.get_text(strip=True) if title_elem else f"Section {section_num}"
            
            # Extract main content
            content_div = soup.find('div', {'id': 'documentContent'}) or soup.find('div', class_='content')
            
            if not content_div:
                logger.warning(f"Could not find content for section {section_num}")
                return None
            
            # Extract subsections
            subsections = []
            for p in content_div.find_all(['p', 'div'], recursive=False):
                text = p.get_text(strip=True)
                if text:
                    # Try to identify subsection markers
                    subsection_match = re.match(r'\(([a-z0-9]+)\)', text)
                    subsections.append({
                        'subsection': subsection_match.group(1) if subsection_match else None,
                        'text': text
                    })
            
            # Extract notes and effective dates
            notes = []
            for note in soup.find_all('div', class_='note'):
                notes.append(note.get_text(strip=True))
            
            section_data = {
                'section_number': section_num,
                'title': title,
                'url': section_url,
                'subsections': subsections,
                'full_text': content_div.get_text(strip=True),
                'notes': notes,
                'scraped_date': datetime.now().isoformat()
            }
            
            return section_data
            
        except Exception as e:
            logger.error(f"Error scraping section {section_num}: {e}")
            return None
    
    def scrape_all_sections(self, max_sections: Optional[int] = None) -> List[Dict]:
        """
        Scrape all sections of Title 26
        
        Args:
            max_sections: Limit number of sections (for testing)
        """
        all_sections = []
        chapters = self.get_chapter_list()
        
        total_scraped = 0
        
        for chapter in chapters:
            if max_sections and total_scraped >= max_sections:
                break
                
            logger.info(f"Processing Chapter {chapter['number']}: {chapter['title']}")
            sections = self.get_sections_in_chapter(chapter['url'])
            
            for section in sections:
                if max_sections and total_scraped >= max_sections:
                    break
                
                section_data = self.scrape_section(section['url'], section['number'])
                
                if section_data:
                    section_data['chapter'] = chapter['number']
                    section_data['chapter_title'] = chapter['title']
                    all_sections.append(section_data)
                    
                    # Save incrementally
                    self._save_section(section_data)
                    total_scraped += 1
                    
                    if total_scraped % 10 == 0:
                        logger.info(f"Progress: {total_scraped} sections scraped")
        
        # Save consolidated file
        self._save_all_sections(all_sections)
        logger.info(f"Complete! Scraped {len(all_sections)} sections")
        
        return all_sections
    
    def _save_section(self, section_data: Dict):
        """Save individual section to file"""
        section_num = section_data['section_number']
        filepath = self.OUTPUT_DIR / f"section_{section_num}.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(section_data, f, indent=2, ensure_ascii=False)
    
    def _save_all_sections(self, sections: List[Dict]):
        """Save all sections to consolidated file"""
        filepath = self.OUTPUT_DIR / "all_sections.jsonl"
        with open(filepath, 'w', encoding='utf-8') as f:
            for section in sections:
                f.write(json.dumps(section, ensure_ascii=False) + '\n')
        
        # Also save metadata summary
        summary = {
            'total_sections': len(sections),
            'sections': [
                {
                    'number': s['section_number'],
                    'title': s['title'],
                    'chapter': s['chapter']
                }
                for s in sections
            ],
            'scraped_date': datetime.now().isoformat()
        }
        
        with open(self.OUTPUT_DIR / "summary.json", 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)


class IRSPublicationScraper:
    """Scrape IRS publications and forms"""
    
    BASE_URL = "https://www.irs.gov"
    FORMS_URL = "https://www.irs.gov/forms-instructions"
    OUTPUT_DIR = Path("data/raw/federal/irs_publications")
    
    def __init__(self, rate_limit: float = 1.0):
        self.rate_limit = rate_limit
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Research/Educational Tax IR System)'
        })
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    def get_publication_list(self, year: int = 2024) -> List[Dict]:
        """Get list of IRS publications for a given year"""
        
        # Common IRS publications relevant for tax scenarios
        publications = [
            {'number': '17', 'title': 'Your Federal Income Tax'},
            {'number': '334', 'title': 'Tax Guide for Small Business'},
            {'number': '463', 'title': 'Travel, Gift, and Car Expenses'},
            {'number': '501', 'title': 'Dependents, Standard Deduction, and Filing Information'},
            {'number': '502', 'title': 'Medical and Dental Expenses'},
            {'number': '504', 'title': 'Divorced or Separated Individuals'},
            {'number': '525', 'title': 'Taxable and Nontaxable Income'},
            {'number': '527', 'title': 'Residential Rental Property'},
            {'number': '535', 'title': 'Business Expenses'},
            {'number': '550', 'title': 'Investment Income and Expenses'},
            {'number': '590-A', 'title': 'Contributions to Individual Retirement Arrangements'},
            {'number': '590-B', 'title': 'Distributions from Individual Retirement Arrangements'},
        ]
        
        for pub in publications:
            pub['url'] = f"{self.BASE_URL}/pub/irs-pdf/p{pub['number']}.pdf"
            pub['year'] = year
        
        return publications
    
    def download_publication(self, pub_info: Dict) -> Optional[Path]:
        """Download a single IRS publication PDF"""
        time.sleep(self.rate_limit)
        
        try:
            logger.info(f"Downloading Publication {pub_info['number']}...")
            response = self.session.get(pub_info['url'], stream=True)
            response.raise_for_status()
            
            filename = f"pub_{pub_info['number']}_{pub_info['year']}.pdf"
            filepath = self.OUTPUT_DIR / filename
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Saved to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error downloading publication {pub_info['number']}: {e}")
            return None
    
    def download_all_publications(self, year: int = 2024):
        """Download all key IRS publications"""
        publications = self.get_publication_list(year)
        
        downloaded = []
        for pub in publications:
            filepath = self.download_publication(pub)
            if filepath:
                downloaded.append({
                    'number': pub['number'],
                    'title': pub['title'],
                    'year': year,
                    'filepath': str(filepath)
                })
        
        # Save metadata
        with open(self.OUTPUT_DIR / f"publications_{year}.json", 'w') as f:
            json.dump(downloaded, f, indent=2)
        
        logger.info(f"Downloaded {len(downloaded)} publications")


def main():
    """Main execution function"""
    
    print("=" * 60)
    print("Federal Tax Code Scraper")
    print("=" * 60)
    print()
    print("This script will scrape:")
    print("1. IRC Title 26 sections from Cornell LII")
    print("2. IRS Publications (PDFs)")
    print()
    print("MANUAL STEPS REQUIRED:")
    print("- For IRS Publications: You may need to manually verify PDF links")
    print("- Some sections may require CAPTCHA solving")
    print("- Rate limiting is set to 1 second between requests")
    print()
    
    choice = input("What would you like to scrape?\n1. IRC Sections (full)\n2. IRC Sections (test - first 20)\n3. IRS Publications\n4. All\nChoice (1-4): ")
    
    if choice in ['1', '2', '4']:
        scraper = FederalTaxScraper(rate_limit=1.0)
        max_sections = 20 if choice == '2' else None
        scraper.scrape_all_sections(max_sections=max_sections)
    
    if choice in ['3', '4']:
        pub_scraper = IRSPublicationScraper(rate_limit=1.0)
        year = input("Enter year (default 2024): ").strip() or "2024"
        pub_scraper.download_all_publications(year=int(year))
    
    print("\nScraping complete! Check data/raw/federal/ for output.")


if __name__ == "__main__":
    main()
