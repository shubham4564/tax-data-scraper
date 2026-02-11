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


# State tax website configurations - All 50 States + DC
# Updated: 2026-02-10 with verified URLs
STATE_CONFIGS = {
    'alabama': {
        'name': 'Alabama',
        'base_url': 'https://casetext.com/statute/code-of-alabama/title-40-revenue-and-taxation',
        'alternate_url': 'https://revenue.alabama.gov/laws-rules/',
        'type': 'manual',  # PDF downloads required
        'tax_types': ['income', 'sales', 'property'],
        'notes': 'Title 40 - Revenue and Taxation. Requires manual download from state revenue site.'
    },
    'alaska': {
        'name': 'Alaska',
        'base_url': 'http://www.akleg.gov/basis/statutes.asp',
        'title': '43',  # Title 43 - Revenue and Taxation
        'type': 'structured',
        'tax_types': ['corporate', 'oil_gas', 'property'],  # No state income tax
        'notes': 'No state income or sales tax. Focus on corporate, oil/gas, and property taxes.'
    },
    'arizona': {
        'name': 'Arizona',
        'base_url': 'https://www.azleg.gov/arsDetail/',
        'title': '42',  # Title 42 - Taxation
        'type': 'structured',
        'tax_types': ['income', 'sales', 'property'],
        'notes': 'Arizona Revised Statutes Title 42'
    },
    'arkansas': {
        'name': 'Arkansas',
        'base_url': 'https://casetext.com/statute/arkansas-code/title-26-taxation',
        'alternate_url': 'https://www.dfa.arkansas.gov/income-tax/tax-law-regs-and-court-cases/',
        'type': 'manual',
        'tax_types': ['income', 'sales', 'property'],
        'notes': 'Arkansas Code Title 26. PDF downloads recommended.'
    },
    'california': {
        'name': 'California',
        'base_url': 'https://leginfo.legislature.ca.gov/faces/codes.xhtml',
        'tax_codes': ['RTC'],  # Revenue and Taxation Code
        'ftb_url': 'https://www.ftb.ca.gov/tax-pros/law/',
        'type': 'manual',  # Interactive site, manual download recommended
        'tax_types': ['income', 'sales', 'property', 'corporate'],
        'notes': 'Revenue and Taxation Code. Use FTB website for PDFs.'
    },
    'colorado': {
        'name': 'Colorado',
        'base_url': 'https://advance.lexis.com/container?config=014CJAA5ZGVhZjA3NS02MmMzLTRlZWQtOGJjNC00YzQ1MmZlNzc2YWYKAFBvZENhdGFsb2e9wTnJ',
        'alternate_url': 'https://tax.colorado.gov/tax-law',
        'title': '39',  # Title 39 - Taxation
        'type': 'structured',
        'tax_types': ['income', 'sales', 'property'],
        'notes': 'Colorado Revised Statutes Title 39'
    },
    'connecticut': {
        'name': 'Connecticut',
        'base_url': 'https://www.cga.ct.gov/current/pub/titles.htm',
        'title': '12',  # Title 12 - Taxation
        'type': 'structured',
        'tax_types': ['income', 'sales', 'property', 'corporate'],
        'notes': 'Connecticut General Statutes Title 12'
    },
    'delaware': {
        'name': 'Delaware',
        'base_url': 'https://delcode.delaware.gov/title30/',
        'title': '30',  # Title 30 - State Taxes
        'type': 'structured',
        'tax_types': ['income', 'corporate', 'gross_receipts'],  # No sales tax
        'notes': 'Delaware Code Title 30. No general sales tax.'
    },
    'florida': {
        'name': 'Florida',
        'base_url': 'http://www.leg.state.fl.us/statutes/',
        'chapters': ['212', '220', '193', '197'],  # Sales, Corporate, Property Assessment, Property Tax
        'type': 'structured',
        'tax_types': ['sales', 'corporate', 'property'],  # No state income tax
        'notes': 'Florida Statutes. No state income tax.'
    },
    'georgia': {
        'name': 'Georgia',
        'base_url': 'https://law.justia.com/codes/georgia/2022/title-48/',
        'alternate_url': 'https://dor.georgia.gov/laws-rules-and-policies',
        'title': '48',  # Title 48 - Revenue and Taxation
        'type': 'structured',
        'tax_types': ['income', 'sales', 'property', 'corporate'],
        'notes': 'Georgia Code Title 48'
    },
    'hawaii': {
        'name': 'Hawaii',
        'base_url': 'https://www.capitol.hawaii.gov/hrscurrent/',
        'title': '235',  # Income Tax Law
        'chapters': ['235', '237', '238'],  # Income, GET, Franchise
        'type': 'structured',
        'tax_types': ['income', 'get', 'corporate'],
        'notes': 'Hawaii Revised Statutes. Chapter 235 (Income), 237 (GET), 238 (Franchise)'
    },
    'idaho': {
        'name': 'Idaho',
        'base_url': 'https://legislature.idaho.gov/statutesrules/idstat/',
        'title': '63',  # Title 63 - Revenue and Taxation
        'type': 'structured',
        'tax_types': ['income', 'sales', 'property'],
        'notes': 'Idaho Statutes Title 63'
    },
    'illinois': {
        'name': 'Illinois',
        'base_url': 'https://www.ilga.gov/legislation/ilcs/ilcs.asp',
        'codes': ['35 ILCS 5', '35 ILCS 105', '35 ILCS 120'],  # Income, Use Tax, Retailers' Occupation Tax
        'type': 'structured',
        'tax_types': ['income', 'sales', 'property', 'corporate'],
        'notes': 'Illinois Compiled Statutes - Chapter 35 (Revenue)'
    },
    'indiana': {
        'name': 'Indiana',
        'base_url': 'https://iga.in.gov/laws/2023/ic/titles/6',
        'title': '6',  # Title 6 - Taxation
        'type': 'structured',
        'tax_types': ['income', 'sales', 'property', 'corporate'],
        'notes': 'Indiana Code Title 6'
    },
    'iowa': {
        'name': 'Iowa',
        'base_url': 'https://www.legis.iowa.gov/law/statutory',
        'title': '422',  # Income, Sales, Use, Franchise
        'type': 'structured',
        'tax_types': ['income', 'sales', 'property', 'corporate'],
        'notes': 'Iowa Code Chapter 422 and related chapters'
    },
    'kansas': {
        'name': 'Kansas',
        'base_url': 'https://www.ksrevisor.org/statutes/chapters/ch79/',
        'chapter': '79',  # Taxation
        'type': 'structured',
        'tax_types': ['income', 'sales', 'property'],
        'notes': 'Kansas Statutes Annotated Chapter 79'
    },
    'kentucky': {
        'name': 'Kentucky',
        'base_url': 'https://apps.legislature.ky.gov/law/statutes',
        'chapters': ['141', '139'],  # Income Tax, Property Tax
        'type': 'structured',
        'tax_types': ['income', 'sales', 'property', 'corporate'],
        'notes': 'Kentucky Revised Statutes - Chapters 139-142'
    },
    'louisiana': {
        'name': 'Louisiana',
        'base_url': 'https://legis.la.gov/Legis/Laws_Toc.aspx?folder=67',
        'title': '47',  # Revenue and Taxation
        'type': 'structured',
        'tax_types': ['income', 'sales', 'property', 'corporate'],
        'notes': 'Louisiana Revised Statutes Title 47'
    },
    'maine': {
        'name': 'Maine',
        'base_url': 'https://legislature.maine.gov/statutes/36/title36sec0.html',
        'title': '36',  # Taxation
        'type': 'structured',
        'tax_types': ['income', 'sales', 'property'],
        'notes': 'Maine Revised Statutes Title 36'
    },
    'maryland': {
        'name': 'Maryland',
        'base_url': 'https://mgaleg.maryland.gov/mgawebsite/Laws/StatutesConstitution',
        'article': 'Tax-General',
        'type': 'structured',
        'tax_types': ['income', 'sales', 'property', 'corporate'],
        'notes': 'Annotated Code of Maryland - Tax-General Article'
    },
    'massachusetts': {
        'name': 'Massachusetts',
        'base_url': 'https://malegislature.gov/Laws/GeneralLaws',
        'chapters': ['62', '63', '64'],  # Income, Corporate, Sales/Use
        'type': 'structured',
        'tax_types': ['income', 'sales', 'property', 'corporate'],
        'notes': 'Massachusetts General Laws Chapters 59-65A (Taxation)'
    },
    'michigan': {
        'name': 'Michigan',
        'base_url': 'https://www.legislature.mi.gov/Law/ChapterIndex',
        'acts': ['Income Tax Act', 'General Sales Tax Act'],
        'type': 'structured',
        'tax_types': ['income', 'sales', 'property', 'corporate'],
        'notes': 'Michigan Compiled Laws - Various tax acts'
    },
    'minnesota': {
        'name': 'Minnesota',
        'base_url': 'https://www.revisor.mn.gov/statutes/',
        'chapters': ['290', '297A'],  # Income/Corporate, Sales/Use
        'type': 'structured',
        'tax_types': ['income', 'sales', 'property', 'corporate'],
        'notes': 'Minnesota Statutes Chapters 289A-297I (Taxation)'
    },
    'mississippi': {
        'name': 'Mississippi',
        'base_url': 'https://law.justia.com/codes/mississippi/2022/title-27/',
        'title': '27',  # Taxation and Finance
        'type': 'manual',
        'tax_types': ['income', 'sales', 'property'],
        'notes': 'Mississippi Code Title 27'
    },
    'missouri': {
        'name': 'Missouri',
        'base_url': 'https://revisor.mo.gov/main/Home.aspx',
        'title': '143',  # Income Tax
        'chapters': ['143', '144'],  # Income, Sales
        'type': 'structured',
        'tax_types': ['income', 'sales', 'property', 'corporate'],
        'notes': 'Missouri Revised Statutes - Chapters 143-154 (Revenue and Taxation)'
    },
    'montana': {
        'name': 'Montana',
        'base_url': 'https://leg.mt.gov/bills/mca/title_0150/chapters_index.html',
        'title': '15',  # Taxation
        'type': 'structured',
        'tax_types': ['income', 'property', 'corporate'],  # No general sales tax
        'notes': 'Montana Code Annotated Title 15. No general sales tax.'
    },
    'nebraska': {
        'name': 'Nebraska',
        'base_url': 'https://nebraskalegislature.gov/laws/browse-chapters.php',
        'chapters': ['77'],  # Revenue and Taxation
        'type': 'structured',
        'tax_types': ['income', 'sales', 'property'],
        'notes': 'Nebraska Revised Statutes Chapter 77'
    },
    'nevada': {
        'name': 'Nevada',
        'base_url': 'https://www.leg.state.nv.us/nrs/',
        'chapters': ['363', '372', '374', '375'],  # Various business taxes, sales
        'type': 'structured',
        'tax_types': ['sales', 'property', 'business'],  # No state income tax
        'notes': 'Nevada Revised Statutes. No state income tax.'
    },
    'new_hampshire': {
        'name': 'New Hampshire',
        'base_url': 'https://www.gencourt.state.nh.us/rsa/html/indexes/default.html',
        'titles': ['77', '78'],  # Property, Business taxes
        'type': 'structured',
        'tax_types': ['property', 'business'],  # No income or sales tax
        'notes': 'New Hampshire RSA. No income or general sales tax.'
    },
    'new_jersey': {
        'name': 'New Jersey',
        'base_url': 'https://lis.njleg.state.nj.us/nxt/gateway.dll?f=templates&fn=default.htm',
        'titles': ['54', '54A'],  # Taxation, Gross Income Tax
        'type': 'structured',
        'tax_types': ['income', 'sales', 'property', 'corporate'],
        'notes': 'New Jersey Statutes Titles 54-54A'
    },
    'new_mexico': {
        'name': 'New Mexico',
        'base_url': 'https://nmonesource.com/nmos/nmsa/en/nav.do',
        'chapter': '7',  # Taxation
        'type': 'manual',
        'tax_types': ['income', 'gross_receipts', 'property'],
        'notes': 'New Mexico Statutes Annotated Chapter 7'
    },
    'new_york': {
        'name': 'New York',
        'base_url': 'https://www.nysenate.gov/legislation/laws/TAX',
        'type': 'structured',
        'tax_types': ['income', 'sales', 'property', 'corporate'],
        'notes': 'New York Tax Law - Comprehensive online access'
    },
    'north_carolina': {
        'name': 'North Carolina',
        'base_url': 'https://www.ncleg.gov/Laws/GeneralStatutes',
        'chapter': '105',  # Taxation
        'type': 'structured',
        'tax_types': ['income', 'sales', 'property', 'corporate'],
        'notes': 'North Carolina General Statutes Chapter 105'
    },
    'north_dakota': {
        'name': 'North Dakota',
        'base_url': 'https://www.legis.nd.gov/general-information/north-dakota-century-code',
        'title': '57',  # Taxation
        'type': 'structured',
        'tax_types': ['income', 'sales', 'property'],
        'notes': 'North Dakota Century Code Title 57'
    },
    'ohio': {
        'name': 'Ohio',
        'base_url': 'https://codes.ohio.gov/ohio-revised-code',
        'titles': ['5747', '5739'],  # Income, Sales/Use
        'type': 'structured',
        'tax_types': ['income', 'sales', 'property', 'cat'],  # Commercial Activity Tax
        'notes': 'Ohio Revised Code Titles 57 (Taxation)'
    },
    'oklahoma': {
        'name': 'Oklahoma',
        'base_url': 'https://www.oscn.net/applications/oscn/Index.asp?ftdb=STOKST68',
        'title': '68',  # Revenue and Taxation
        'type': 'structured',
        'tax_types': ['income', 'sales', 'property'],
        'notes': 'Oklahoma Statutes Title 68'
    },
    'oregon': {
        'name': 'Oregon',
        'base_url': 'https://www.oregonlegislature.gov/bills_laws/Pages/ORS.aspx',
        'chapters': ['316', '317', '318'],  # Personal Income, Corporate, Estate
        'type': 'structured',
        'tax_types': ['income', 'property', 'corporate'],  # No sales tax
        'notes': 'Oregon Revised Statutes. No sales tax.'
    },
    'pennsylvania': {
        'name': 'Pennsylvania',
        'base_url': 'https://www.legis.state.pa.us/cfdocs/legis/LI/consCheck.cfm?tabType=1',
        'title': '72',  # Taxation and Fiscal Affairs
        'type': 'manual',
        'tax_types': ['income', 'sales', 'property', 'corporate'],
        'notes': 'Pennsylvania Consolidated Statutes Title 72'
    },
    'rhode_island': {
        'name': 'Rhode Island',
        'base_url': 'https://webserver.rilegislature.gov/Statutes/',
        'title': '44',  # Taxation
        'type': 'structured',
        'tax_types': ['income', 'sales', 'property', 'corporate'],
        'notes': 'Rhode Island General Laws Title 44'
    },
    'south_carolina': {
        'name': 'South Carolina',
        'base_url': 'https://www.scstatehouse.gov/code/statmast.php',
        'title': '12',  # Taxation
        'type': 'structured',
        'tax_types': ['income', 'sales', 'property'],
        'notes': 'South Carolina Code of Laws Title 12'
    },
    'south_dakota': {
        'name': 'South Dakota',
        'base_url': 'https://sdlegislature.gov/Statutes/Codified_Laws',
        'title': '10',  # Taxation
        'type': 'structured',
        'tax_types': ['sales', 'property'],  # No income tax
        'notes': 'South Dakota Codified Laws Title 10. No income tax.'
    },
    'tennessee': {
        'name': 'Tennessee',
        'base_url': 'https://www.tn.gov/revenue/taxes.html',
        'alternate_url': 'https://law.justia.com/codes/tennessee/2022/title-67/',
        'title': '67',  # Taxes and Licenses
        'type': 'manual',
        'tax_types': ['sales', 'property', 'franchise'],  # No broad-based income tax
        'notes': 'Tennessee Code Title 67. No individual income tax (except interest/dividends).'
    },
    'texas': {
        'name': 'Texas',
        'base_url': 'https://statutes.capitol.texas.gov',
        'tax_codes': ['TX'],  # Tax Code
        'type': 'structured',
        'tax_types': ['sales', 'property', 'franchise'],  # No income tax
        'notes': 'Texas Tax Code. No state income tax.'
    },
    'utah': {
        'name': 'Utah',
        'base_url': 'https://le.utah.gov/xcode/code.html',
        'title': '59',  # Revenue and Taxation
        'type': 'structured',
        'tax_types': ['income', 'sales', 'property'],
        'notes': 'Utah Code Title 59'
    },
    'vermont': {
        'name': 'Vermont',
        'base_url': 'https://legislature.vermont.gov/statutes/',
        'title': '32',  # Taxation and Finance
        'type': 'structured',
        'tax_types': ['income', 'sales', 'property'],
        'notes': 'Vermont Statutes Title 32'
    },
    'virginia': {
        'name': 'Virginia',
        'base_url': 'https://law.lis.virginia.gov/vacode/',
        'title': '58.1',  # Taxation
        'type': 'structured',
        'tax_types': ['income', 'sales', 'property', 'corporate'],
        'notes': 'Code of Virginia Title 58.1'
    },
    'washington': {
        'name': 'Washington',
        'base_url': 'https://app.leg.wa.gov/rcw/',
        'title': '82',  # Excise Taxes
        'type': 'structured',
        'tax_types': ['sales', 'property', 'b&o'],  # No income tax
        'notes': 'Revised Code of Washington Title 82. No income tax.'
    },
    'west_virginia': {
        'name': 'West Virginia',
        'base_url': 'https://code.wvlegislature.gov/code.cfm',
        'chapter': '11',  # Taxation
        'type': 'structured',
        'tax_types': ['income', 'sales', 'property', 'corporate'],
        'notes': 'West Virginia Code Chapter 11'
    },
    'wisconsin': {
        'name': 'Wisconsin',
        'base_url': 'https://docs.legis.wisconsin.gov/statutes/statutes',
        'chapters': ['71', '77'],  # Income, Sales/Use
        'type': 'structured',
        'tax_types': ['income', 'sales', 'property', 'corporate'],
        'notes': 'Wisconsin Statutes Chapters 70-79 (Taxation)'
    },
    'wyoming': {
        'name': 'Wyoming',
        'base_url': 'https://www.wyoleg.gov/statutes/compress/title39.pdf',
        'alternate_url': 'https://law.justia.com/codes/wyoming/2022/title-39/',
        'title': '39',  # Taxation and Revenue
        'type': 'manual',
        'tax_types': ['sales', 'property', 'severance'],  # No income tax
        'notes': 'Wyoming Statutes Title 39. No income tax. PDF download.'
    },
    'district_of_columbia': {
        'name': 'District of Columbia',
        'base_url': 'https://code.dccouncil.gov/us/dc/council/code/titles/47',
        'title': '47',  # Taxation and Fiscal Affairs
        'type': 'structured',
        'tax_types': ['income', 'sales', 'property', 'corporate'],
        'notes': 'DC Code Title 47'
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


class GenericStateScraper(BaseStateScraper):
    """Generic scraper for states with structured online codes"""
    
    def scrape(self, max_sections: Optional[int] = None) -> List[Dict]:
        """
        Attempt to scrape state tax code using generic patterns
        Falls back to manual instructions if automated scraping fails
        """
        logger.info(f"Starting {self.state_name} tax code scraping...")
        
        config_type = self.config.get('type', 'manual')
        
        if config_type == 'manual':
            return self._create_manual_instructions()
        
        # Try automated scraping for 'structured' types
        try:
            return self._attempt_generic_scrape(max_sections)
        except Exception as e:
            logger.warning(f"Automated scraping failed for {self.state_name}: {e}")
            logger.warning("Falling back to manual instructions...")
            return self._create_manual_instructions()
    
    def _attempt_generic_scrape(self, max_sections: Optional[int] = None) -> List[Dict]:
        """Attempt generic scraping approach"""
        base_url = self.config.get('base_url')
        if not base_url:
            raise ValueError("No base URL configured")
        
        time.sleep(self.rate_limit)
        response = self.session.get(base_url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Generic pattern: look for links to tax code sections
        sections = []
        for link in soup.find_all('a', href=True):
            text = link.get_text(strip=True)
            href = link['href']
            
            # Skip empty links or navigation elements
            if not text or len(text) < 3:
                continue
            
            # Look for patterns suggesting tax code sections
            if any(keyword in text.lower() for keyword in ['tax', 'revenue', 'chapter', 'section', 'title']):
                sections.append({
                    'text': text,
                    'url': href if href.startswith('http') else f"{base_url}/{href.lstrip('/')}"
                })
        
        # If we found sections, save metadata
        if sections:
            result = {
                'state': self.state_name,
                'sections_found': len(sections),
                'sections': sections[:max_sections] if max_sections else sections,
                'base_url': base_url,
                'scraped_date': datetime.now().isoformat(),
                'note': 'Generic scraping - sections may need validation'
            }
            
            self._save_section(result, 'generic_scrape_result.json')
            logger.info(f"Found {len(sections)} potential sections")
            return [result]
        
        raise ValueError("No sections found with generic patterns")
    
    def _create_manual_instructions(self) -> List[Dict]:
        """Create manual download instructions for states requiring manual intervention"""
        
        manual_instructions = {
            'state': self.state_name,
            'instruction': 'MANUAL DOWNLOAD/NAVIGATION REQUIRED',
            'url': self.config.get('base_url', 'N/A'),
            'alternate_url': self.config.get('alternate_url', 'N/A'),
            'tax_types': self.config.get('tax_types', []),
            'steps': self._generate_manual_steps(),
            'notes': self.config.get('notes', ''),
            'output_directory': str(self.output_dir),
            'created_date': datetime.now().isoformat()
        }
        
        with open(self.output_dir / 'MANUAL_DOWNLOAD_INSTRUCTIONS.json', 'w') as f:
            json.dump(manual_instructions, f, indent=2)
        
        logger.warning(f"{self.state_name} requires manual download. See MANUAL_DOWNLOAD_INSTRUCTIONS.json")
        return []
    
    def _generate_manual_steps(self) -> List[str]:
        """Generate state-specific manual download steps"""
        base_url = self.config.get('base_url', 'N/A')
        title = self.config.get('title') or self.config.get('chapter') or self.config.get('titles', ['N/A'])[0]
        
        steps = [
            f"1. Navigate to {base_url}",
            f"2. Look for tax/revenue code (Title/Chapter {title})",
            "3. Download PDF or HTML versions of tax statutes",
            "4. Focus on tax types: " + ', '.join(self.config.get('tax_types', ['all'])),
            f"5. Save files to: {self.output_dir}",
            "6. Note: You may need to browse multiple chapters/sections",
            "7. Verify completeness: check for income, sales, property tax sections"
        ]
        
        if self.config.get('alternate_url'):
            steps.insert(1, f"   Alternative URL: {self.config['alternate_url']}")
        
        return steps


class StateTaxScraperManager:
    """Manages scraping across multiple states"""
    
    def __init__(self):
        # Map specific states to specialized scrapers
        self.specialized_scrapers = {
            'california': CaliforniaScraper,
            'new_york': NewYorkScraper,
            'texas': TexasScraper,
            'florida': FloridaScraper
        }
    
    def get_scraper(self, state_key: str):
        """Get appropriate scraper for state"""
        if state_key not in STATE_CONFIGS:
            logger.error(f"Unknown state: {state_key}")
            return None
        
        config = STATE_CONFIGS[state_key]
        
        # Use specialized scraper if available
        if state_key in self.specialized_scrapers:
            return self.specialized_scrapers[state_key](config)
        
        # Use generic scraper for other states
        return GenericStateScraper(config)
    
    def scrape_state(self, state_key: str, max_sections: Optional[int] = None) -> List[Dict]:
        """Scrape a specific state's tax code"""
        scraper = self.get_scraper(state_key)
        if not scraper:
            return []
        
        return scraper.scrape(max_sections=max_sections)
    
    def scrape_all_states(self, max_sections_per_state: Optional[int] = None):
        """Scrape all configured states"""
        results = {}
        
        for state_key in sorted(STATE_CONFIGS.keys()):
            logger.info(f"\n{'='*60}\nScraping {STATE_CONFIGS[state_key]['name'].upper()}\n{'='*60}")
            try:
                results[state_key] = self.scrape_state(state_key, max_sections_per_state)
            except Exception as e:
                logger.error(f"Failed to scrape {state_key}: {e}")
                results[state_key] = []
            time.sleep(2)  # Extra delay between states
        
        # Save summary
        summary = {
            'total_states': len(STATE_CONFIGS),
            'states_attempted': list(results.keys()),
            'successful_scrapes': [k for k, v in results.items() if v],
            'failed_or_manual': [k for k, v in results.items() if not v],
            'total_sections': sum(len(v) for v in results.values()),
            'by_state': {k: len(v) for k, v in results.items()},
            'scraped_date': datetime.now().isoformat()
        }
        
        with open('data/raw/states/scraping_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"SCRAPING COMPLETE")
        logger.info(f"{'='*60}")
        logger.info(f"Total states attempted: {len(results)}")
        logger.info(f"Successful: {len(summary['successful_scrapes'])}")
        logger.info(f"Manual/Failed: {len(summary['failed_or_manual'])}")
        logger.info(f"Total sections: {summary['total_sections']}")
        
        return results
    
    def list_states(self):
        """List all available states with their configurations"""
        print(f"\n{'='*80}")
        print(f"ALL 50 STATES + DC - TAX CODE SCRAPING CONFIGURATIONS")
        print(f"{'='*80}\n")
        
        for i, (key, config) in enumerate(sorted(STATE_CONFIGS.items()), 1):
            status = "✓ Automated" if config.get('type') == 'structured' else "⚠ Manual"
            tax_types = ', '.join(config.get('tax_types', []))
            print(f"{i:2d}. {config['name']:20s} [{status}] - {tax_types}")
            print(f"    URL: {config.get('base_url', 'N/A')}")
            print(f"    Notes: {config.get('notes', 'N/A')}")
            print()
        
        print(f"{'='*80}")
        print(f"Legend:")
        print(f"  ✓ Automated = Can scrape directly (may still require validation)")
        print(f"  ⚠ Manual    = Requires manual download or interactive site navigation")
        print(f"{'='*80}\n")


def main():
    """Main execution"""
    print("=" * 80)
    print("STATE TAX CODE SCRAPER - ALL 50 STATES + DC")
    print("=" * 80)
    print()
    print("This script scrapes state tax codes from official legislative websites.")
    print()
    print(f"Total states configured: {len(STATE_CONFIGS)}")
    print()
    print("IMPORTANT NOTES:")
    print("- Some states support automated scraping (✓ structured)")
    print("- Other states require manual download (⚠ manual)")
    print("- Manual states will generate download instructions")
    print("- Rate limiting: 1.5 seconds between requests")
    print("- Always respect robots.txt and terms of service")
    print()
    
    manager = StateTaxScraperManager()
    
    print("OPTIONS:")
    print("1. List all states and their configurations")
    print("2. Scrape all states (automated + manual instructions)")
    print("3. Scrape only automated states (skip manual)")
    print("4. Scrape specific state")
    print("5. Test mode (5 sections per state)")
    print()
    
    choice = input("Enter choice (1-5): ").strip()
    
    if choice == '1':
        manager.list_states()
        
    elif choice == '2':
        print("\nStarting full scrape of all 50 states + DC...")
        confirm = input("This may take 30-60 minutes. Continue? [y/n]: ").lower()
        if confirm == 'y':
            manager.scrape_all_states()
        else:
            print("Cancelled.")
    
    elif choice == '3':
        print("\nScraping only automated states...")
        automated_states = [k for k, v in STATE_CONFIGS.items() if v.get('type') == 'structured']
        print(f"Found {len(automated_states)} automated states")
        
        results = {}
        for state_key in automated_states:
            logger.info(f"\n{'='*60}\nScraping {STATE_CONFIGS[state_key]['name']}\n{'='*60}")
            try:
                results[state_key] = manager.scrape_state(state_key)
            except Exception as e:
                logger.error(f"Failed: {e}")
                results[state_key] = []
            time.sleep(2)
        
        print(f"\nCompleted {len([r for r in results.values() if r])} successful scrapes")
    
    elif choice == '4':
        manager.list_states()
        state = input("\nEnter state key (e.g., california, new_york, texas): ").lower().strip()
        
        if state in STATE_CONFIGS:
            config = STATE_CONFIGS[state]
            print(f"\nScraping {config['name']}...")
            print(f"Type: {config.get('type', 'unknown')}")
            print(f"URL: {config.get('base_url', 'N/A')}")
            print()
            
            max_sections = input("Max sections (blank for all): ").strip()
            max_sections = int(max_sections) if max_sections.isdigit() else None
            
            manager.scrape_state(state, max_sections=max_sections)
        else:
            print(f"Unknown state: {state}")
            print(f"Available: {', '.join(sorted(STATE_CONFIGS.keys()))}")
    
    elif choice == '5':
        print("\nTest mode: scraping first 5 sections per state...")
        manager.scrape_all_states(max_sections_per_state=5)
    
    else:
        print("Invalid choice. Exiting.")
        return
    
    print("\nScraping complete! Check data/raw/states/ for output.")
    print("\nNOTE: States marked as 'manual' will have MANUAL_DOWNLOAD_INSTRUCTIONS.json")
    print("      files in their respective directories with detailed download steps.")


if __name__ == "__main__":
    main()
