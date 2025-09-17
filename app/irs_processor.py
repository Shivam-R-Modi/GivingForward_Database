"""
IRS Data Processing Module
Handles downloading and processing IRS nonprofit data
"""
import csv
import io
import zipfile
import logging
from pathlib import Path
from typing import List, Dict, Optional
import requests
from datetime import datetime
import time

logger = logging.getLogger(__name__)

class IRSDataProcessor:
    """Processes IRS nonprofit data files"""
    
    # IRS data URLs (as of 2024)
    IRS_BASE_URL = "https://www.irs.gov/pub/irs-soi"
    
    # EO BMF (Exempt Organizations Business Master File) regions
    REGIONS = {
        'eo1': 'Northeast Region',
        'eo2': 'Mid-Atlantic and Great Lakes Region', 
        'eo3': 'Gulf Coast and Pacific Region',
        'eo4': 'All Other Areas'
    }
    
    # Asset/Income amount code mappings
    AMOUNT_CODES = {
        '': 0,
        '0': 0,
        '1': 5000,        # $1-9,999
        '2': 25000,       # $10,000-24,999
        '3': 62500,       # $25,000-99,999
        '4': 175000,      # $100,000-249,999
        '5': 375000,      # $250,000-499,999
        '6': 750000,      # $500,000-999,999
        '7': 2500000,     # $1,000,000-4,999,999
        '8': 7500000,     # $5,000,000-9,999,999
        '9': 25000000,    # $10,000,000-49,999,999
        'A': 75000000,    # $50,000,000-99,999,999
        'B': 175000000,   # $100,000,000-249,999,999
        'C': 375000000,   # $250,000,000-499,999,999
        'D': 750000000,   # $500,000,000+
    }
    
    # NTEE Code categories
    NTEE_CATEGORIES = {
        'A': 'Arts, Culture & Humanities',
        'B': 'Education',
        'C': 'Environment',
        'D': 'Animal-Related',
        'E': 'Health Care',
        'F': 'Mental Health & Crisis Intervention',
        'G': 'Diseases, Disorders & Medical Disciplines',
        'H': 'Medical Research',
        'I': 'Crime & Legal-Related',
        'J': 'Employment',
        'K': 'Food, Agriculture & Nutrition',
        'L': 'Housing & Shelter',
        'M': 'Public Safety, Disaster Preparedness & Relief',
        'N': 'Recreation & Sports',
        'O': 'Youth Development',
        'P': 'Human Services',
        'Q': 'International, Foreign Affairs & National Security',
        'R': 'Civil Rights, Social Action & Advocacy',
        'S': 'Community Improvement & Capacity Building',
        'T': 'Philanthropy, Voluntarism & Grantmaking Foundations',
        'U': 'Science & Technology',
        'V': 'Social Science',
        'W': 'Public & Societal Benefit',
        'X': 'Religion-Related',
        'Y': 'Mutual & Membership Benefit',
        'Z': 'Unknown'
    }
    
    def __init__(self, data_dir: Path = None):
        self.data_dir = data_dir or Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        self.raw_dir = self.data_dir / "raw"
        self.processed_dir = self.data_dir / "processed"
        self.raw_dir.mkdir(exist_ok=True)
        self.processed_dir.mkdir(exist_ok=True)
    
    def download_eo_bmf(self, region: str = None) -> Optional[Path]:
        """
        Download IRS EO Business Master File
        If region is None, downloads all regions
        """
        regions_to_download = [region] if region else list(self.REGIONS.keys())
        downloaded_files = []
        
        for reg in regions_to_download:
            url = f"{self.IRS_BASE_URL}/{reg}.csv"
            output_path = self.raw_dir / f"{reg}_{datetime.now():%Y%m%d}.csv"
            
            logger.info(f"Downloading {reg} from {url}")
            
            try:
                response = requests.get(url, stream=True, timeout=30)
                response.raise_for_status()
                
                # Download with progress
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            if total_size > 0:
                                progress = (downloaded / total_size) * 100
                                if downloaded % (1024 * 1024) == 0:  # Log every MB
                                    logger.info(f"{reg}: {progress:.1f}% downloaded")
                
                logger.info(f"Successfully downloaded {reg} to {output_path}")
                downloaded_files.append(output_path)
                
                # Be nice to IRS servers
                time.sleep(1)
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Failed to download {reg}: {e}")
                continue
        
        return downloaded_files
    
    def download_pub78(self) -> Optional[Path]:
        """Download Publication 78 data (organizations eligible for tax-deductible contributions)"""
        url = f"{self.IRS_BASE_URL}/eo_pub78.txt"
        output_path = self.raw_dir / f"pub78_{datetime.now():%Y%m%d}.txt"
        
        try:
            logger.info(f"Downloading Publication 78 from {url}")
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logger.info(f"Downloaded Publication 78 to {output_path}")
            return output_path
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download Publication 78: {e}")
            return None
    
    def parse_eo_bmf(self, filepath: Path) -> List[Dict]:
        """Parse EO Business Master File CSV"""
        organizations = []
        
        logger.info(f"Parsing {filepath}")
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                # EO BMF files use pipe delimiter
                reader = csv.DictReader(f, delimiter='|')
                
                for row_num, row in enumerate(reader, 1):
                    try:
                        org = self._parse_eo_row(row)
                        if org:
                            organizations.append(org)
                        
                        if row_num % 10000 == 0:
                            logger.info(f"Processed {row_num} rows from {filepath.name}")
                            
                    except Exception as e:
                        logger.warning(f"Error parsing row {row_num}: {e}")
                        continue
                
            logger.info(f"Parsed {len(organizations)} organizations from {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to parse {filepath}: {e}")
        
        return organizations
    
    def _parse_eo_row(self, row: Dict) -> Optional[Dict]:
        """Parse a single row from EO BMF file"""
        
        # Skip if no EIN
        ein = row.get('EIN', '').strip()
        if not ein:
            return None
        
        # Parse and clean data
        org = {
            'ein': ein,
            'name': row.get('NAME', '').strip()[:500],  # Limit length
            'street': row.get('STREET', '').strip(),
            'city': row.get('CITY', '').strip(),
            'state': row.get('STATE', '').strip()[:2],
            'zip': row.get('ZIP', '').strip()[:10],
            
            # Classification codes
            'subsection_code': row.get('SUBSECTION', '').strip(),
            'ntee_code': row.get('NTEE_CD', '').strip(),
            'foundation_code': row.get('FOUNDATION', '').strip(),
            
            # Financial data - convert codes to amounts
            'asset_amount': self._parse_amount_code(row.get('ASSET_AMT', '')),
            'income_amount': self._parse_amount_code(row.get('INCOME_AMT', '')),
            'revenue_amount': self._parse_amount_code(row.get('REVENUE_AMT', '')),
            
            # Status
            'tax_exempt_status': row.get('STATUS', '').strip(),
            'ruling_date': row.get('RULING', '').strip(),
            'tax_period': row.get('TAX_PERIOD', '').strip(),
            
            # Additional fields
            'group_exemption': row.get('GEN', '').strip(),
            'deductibility': row.get('DEDUCTIBILITY', '').strip(),
            'activity_codes': row.get('ACTIVITY', '').strip(),
            'organization_code': row.get('ORGANIZATION', '').strip(),
            
            'data_source': 'IRS_EO_BMF'
        }
        
        # Add NTEE category description
        if org['ntee_code']:
            category_code = org['ntee_code'][0] if org['ntee_code'] else 'Z'
            org['ntee_description'] = self.NTEE_CATEGORIES.get(category_code, 'Unknown')
        
        return org
    
    def _parse_amount_code(self, code: str) -> int:
        """Convert IRS amount code to dollar amount"""
        code = str(code).strip().upper()
        return self.AMOUNT_CODES.get(code, 0)
    
    def download_form_990_index(self, year: int = None) -> Optional[Path]:
        """Download Form 990 index file for a given year"""
        if year is None:
            year = datetime.now().year - 1  # Default to previous year
        
        # Try different URL patterns (IRS changes these occasionally)
        urls = [
            f"https://www.irs.gov/charities-non-profits/form-990-series-downloads/{year}",
            f"{self.IRS_BASE_URL}/index_{year}.csv",
            f"{self.IRS_BASE_URL}/index_{year}.json"
        ]
        
        for url in urls:
            try:
                output_path = self.raw_dir / f"form990_index_{year}.csv"
                
                logger.info(f"Trying to download Form 990 index from {url}")
                response = requests.get(url, timeout=30)
                
                if response.status_code == 200:
                    with open(output_path, 'wb') as f:
                        f.write(response.content)
                    
                    logger.info(f"Downloaded Form 990 index to {output_path}")
                    return output_path
                    
            except Exception as e:
                logger.warning(f"Failed to download from {url}: {e}")
                continue
        
        logger.error(f"Could not download Form 990 index for year {year}")
        return None
    
    def process_all_data(self) -> Dict:
        """
        Download and process all available IRS data
        Returns statistics about the processing
        """
        stats = {
            'started_at': datetime.now(),
            'eo_bmf_files': 0,
            'organizations_processed': 0,
            'errors': 0
        }
        
        # Download EO BMF files
        logger.info("Starting IRS data download and processing")
        
        downloaded_files = self.download_eo_bmf()
        
        if downloaded_files:
            stats['eo_bmf_files'] = len(downloaded_files)
            
            # Process each file
            all_organizations = []
            
            for filepath in downloaded_files:
                organizations = self.parse_eo_bmf(filepath)
                all_organizations.extend(organizations)
            
            stats['organizations_processed'] = len(all_organizations)
            
            # Save to processed directory
            output_path = self.processed_dir / f"all_organizations_{datetime.now():%Y%m%d}.json"
            
            # Save as JSON for now (can be imported to database)
            import json
            with open(output_path, 'w') as f:
                json.dump(all_organizations, f)
            
            logger.info(f"Saved {len(all_organizations)} organizations to {output_path}")
        
        # Download Publication 78
        pub78_path = self.download_pub78()
        if pub78_path:
            stats['pub78_downloaded'] = True
        
        stats['completed_at'] = datetime.now()
        stats['duration'] = (stats['completed_at'] - stats['started_at']).total_seconds()
        
        logger.info(f"Processing complete. Stats: {stats}")
        
        return stats, all_organizations if 'all_organizations' in locals() else []

# Create singleton instance
irs_processor = IRSDataProcessor()
