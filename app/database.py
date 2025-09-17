"""
Database operations and models
"""
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages all database operations"""
    
    def __init__(self, db_path: str = "nonprofits.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Get database connection with optimized settings"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        
        # Optimize SQLite performance
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=10000")
        conn.execute("PRAGMA temp_store=MEMORY")
        
        return conn
    
    def init_database(self):
        """Initialize database with all necessary tables"""
        conn = self.get_connection()
        
        # Organizations table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS organizations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ein TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                legal_name TEXT,
                street TEXT,
                city TEXT,
                state TEXT,
                zip TEXT,
                country TEXT DEFAULT 'US',
                
                -- Classification
                ntee_code TEXT,
                ntee_description TEXT,
                subsection_code TEXT,
                foundation_code TEXT,
                organization_type TEXT,
                
                -- Financial
                asset_amount INTEGER DEFAULT 0,
                income_amount INTEGER DEFAULT 0,
                revenue_amount INTEGER DEFAULT 0,
                
                -- Status
                tax_exempt_status TEXT,
                ruling_date TEXT,
                tax_period TEXT,
                revocation_date TEXT,
                
                -- Contact
                website TEXT,
                email TEXT,
                phone TEXT,
                
                -- Metadata
                data_source TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_org_ein ON organizations(ein)",
            "CREATE INDEX IF NOT EXISTS idx_org_name ON organizations(name)",
            "CREATE INDEX IF NOT EXISTS idx_org_state ON organizations(state)",
            "CREATE INDEX IF NOT EXISTS idx_org_city ON organizations(city)",
            "CREATE INDEX IF NOT EXISTS idx_org_ntee ON organizations(ntee_code)",
            "CREATE INDEX IF NOT EXISTS idx_org_revenue ON organizations(revenue_amount)",
            "CREATE INDEX IF NOT EXISTS idx_org_assets ON organizations(asset_amount)"
        ]
        
        for index_sql in indexes:
            conn.execute(index_sql)
        
        # Full-text search table
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS organizations_fts 
            USING fts5(
                ein, 
                name, 
                legal_name,
                city, 
                state,
                content=organizations,
                content_rowid=id,
                tokenize='porter unicode61'
            )
        """)
        
        # Triggers to keep FTS index updated
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS org_fts_insert
            AFTER INSERT ON organizations
            BEGIN
                INSERT INTO organizations_fts(rowid, ein, name, legal_name, city, state)
                VALUES (new.id, new.ein, new.name, new.legal_name, new.city, new.state);
            END
        """)
        
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS org_fts_update
            AFTER UPDATE ON organizations
            BEGIN
                UPDATE organizations_fts 
                SET ein = new.ein, 
                    name = new.name,
                    legal_name = new.legal_name,
                    city = new.city,
                    state = new.state
                WHERE rowid = new.id;
            END
        """)
        
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS org_fts_delete
            AFTER DELETE ON organizations
            BEGIN
                DELETE FROM organizations_fts WHERE rowid = old.id;
            END
        """)
        
        # Form 990 filings table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS filings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                organization_id INTEGER,
                ein TEXT,
                
                -- Filing identifiers
                object_id TEXT UNIQUE,
                return_id TEXT,
                
                -- Filing info
                form_type TEXT,
                tax_year INTEGER,
                filing_date TEXT,
                
                -- Financial data
                total_revenue INTEGER,
                total_expenses INTEGER,
                total_assets INTEGER,
                total_liabilities INTEGER,
                net_assets INTEGER,
                
                -- Raw data
                xml_url TEXT,
                pdf_url TEXT,
                processed BOOLEAN DEFAULT 0,
                
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (organization_id) REFERENCES organizations(id)
            )
        """)
        
        # Personnel table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS personnel (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                organization_id INTEGER,
                filing_id INTEGER,
                
                name TEXT NOT NULL,
                title TEXT,
                compensation INTEGER,
                hours_per_week REAL,
                
                is_officer BOOLEAN DEFAULT 0,
                is_director BOOLEAN DEFAULT 0,
                is_trustee BOOLEAN DEFAULT 0,
                is_key_employee BOOLEAN DEFAULT 0,
                
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (organization_id) REFERENCES organizations(id),
                FOREIGN KEY (filing_id) REFERENCES filings(id)
            )
        """)
        
        # Import log table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS import_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT,
                file_type TEXT,
                records_processed INTEGER,
                records_imported INTEGER,
                errors INTEGER,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                status TEXT,
                error_details TEXT
            )
        """)
        
        conn.commit()
        conn.close()
        
        logger.info(f"Database initialized at {self.db_path}")
    
    def search_organizations(
        self,
        query: Optional[str] = None,
        state: Optional[str] = None,
        city: Optional[str] = None,
        ntee_code: Optional[str] = None,
        min_revenue: Optional[int] = None,
        max_revenue: Optional[int] = None,
        min_assets: Optional[int] = None,
        max_assets: Optional[int] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Dict], int]:
        """
        Search organizations with multiple filters
        Returns (results, total_count)
        """
        conn = self.get_connection()
        
        # Build query
        base_query = "SELECT * FROM organizations WHERE 1=1"
        count_query = "SELECT COUNT(*) as total FROM organizations WHERE 1=1"
        params = []
        
        # Full-text search
        if query:
            base_query = """
                SELECT o.* FROM organizations o
                JOIN organizations_fts fts ON o.id = fts.rowid
                WHERE organizations_fts MATCH ?
            """
            count_query = """
                SELECT COUNT(*) as total FROM organizations o
                JOIN organizations_fts fts ON o.id = fts.rowid
                WHERE organizations_fts MATCH ?
            """
            params.append(query)
        
        # Add filters
        filter_conditions = []
        
        if state:
            filter_conditions.append("state = ?")
            params.append(state)
        
        if city:
            filter_conditions.append("city LIKE ?")
            params.append(f"%{city}%")
        
        if ntee_code:
            filter_conditions.append("ntee_code LIKE ?")
            params.append(f"{ntee_code}%")
        
        if min_revenue is not None:
            filter_conditions.append("revenue_amount >= ?")
            params.append(min_revenue)
        
        if max_revenue is not None:
            filter_conditions.append("revenue_amount <= ?")
            params.append(max_revenue)
        
        if min_assets is not None:
            filter_conditions.append("asset_amount >= ?")
            params.append(min_assets)
        
        if max_assets is not None:
            filter_conditions.append("asset_amount <= ?")
            params.append(max_assets)
        
        # Combine conditions
        if filter_conditions:
            filter_sql = " AND " + " AND ".join(filter_conditions)
            base_query += filter_sql
            count_query += filter_sql
        
        # Get total count
        total = conn.execute(count_query, params).fetchone()['total']
        
        # Add pagination and execute
        base_query += " ORDER BY revenue_amount DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor = conn.execute(base_query, params)
        results = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return results, total
    
    def get_organization(self, ein: str) -> Optional[Dict]:
        """Get single organization by EIN"""
        conn = self.get_connection()
        
        cursor = conn.execute(
            "SELECT * FROM organizations WHERE ein = ?",
            (ein,)
        )
        
        result = cursor.fetchone()
        conn.close()
        
        return dict(result) if result else None
    
    def insert_organizations(self, organizations: List[Dict], batch_size: int = 1000):
        """Bulk insert organizations"""
        conn = self.get_connection()
        
        # Prepare insert statement
        insert_sql = """
            INSERT OR REPLACE INTO organizations 
            (ein, name, legal_name, street, city, state, zip,
             ntee_code, subsection_code, foundation_code,
             asset_amount, income_amount, revenue_amount,
             tax_exempt_status, ruling_date, data_source)
            VALUES 
            (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        # Process in batches
        total_inserted = 0
        
        for i in range(0, len(organizations), batch_size):
            batch = organizations[i:i + batch_size]
            
            # Prepare data tuples
            data_tuples = []
            for org in batch:
                data_tuples.append((
                    org.get('ein'),
                    org.get('name'),
                    org.get('legal_name'),
                    org.get('street'),
                    org.get('city'),
                    org.get('state'),
                    org.get('zip'),
                    org.get('ntee_code'),
                    org.get('subsection_code'),
                    org.get('foundation_code'),
                    org.get('asset_amount', 0),
                    org.get('income_amount', 0),
                    org.get('revenue_amount', 0),
                    org.get('tax_exempt_status'),
                    org.get('ruling_date'),
                    org.get('data_source', 'IRS')
                ))
            
            conn.executemany(insert_sql, data_tuples)
            conn.commit()
            
            total_inserted += len(batch)
            logger.info(f"Inserted batch: {total_inserted} organizations")
        
        conn.close()
        return total_inserted
    
    def get_statistics(self) -> Dict:
        """Get database statistics"""
        conn = self.get_connection()
        
        stats = {}
        
        # Total organizations
        stats['total_organizations'] = conn.execute(
            "SELECT COUNT(*) as count FROM organizations"
        ).fetchone()['count']
        
        # Organizations by state
        state_counts = conn.execute("""
            SELECT state, COUNT(*) as count 
            FROM organizations 
            WHERE state IS NOT NULL
            GROUP BY state 
            ORDER BY count DESC 
            LIMIT 10
        """).fetchall()
        stats['top_states'] = [dict(row) for row in state_counts]
        
        # Organizations by NTEE
        ntee_counts = conn.execute("""
            SELECT 
                SUBSTR(ntee_code, 1, 1) as category,
                COUNT(*) as count 
            FROM organizations 
            WHERE ntee_code IS NOT NULL
            GROUP BY SUBSTR(ntee_code, 1, 1)
            ORDER BY count DESC
        """).fetchall()
        stats['ntee_distribution'] = [dict(row) for row in ntee_counts]
        
        # Revenue distribution
        revenue_ranges = conn.execute("""
            SELECT 
                CASE 
                    WHEN revenue_amount = 0 THEN 'Zero'
                    WHEN revenue_amount < 50000 THEN '<$50K'
                    WHEN revenue_amount < 250000 THEN '$50K-$250K'
                    WHEN revenue_amount < 1000000 THEN '$250K-$1M'
                    WHEN revenue_amount < 5000000 THEN '$1M-$5M'
                    ELSE '>$5M'
                END as range,
                COUNT(*) as count
            FROM organizations
            GROUP BY range
            ORDER BY revenue_amount
        """).fetchall()
        stats['revenue_distribution'] = [dict(row) for row in revenue_ranges]
        
        conn.close()
        
        return stats

# Create singleton instance
db = DatabaseManager()
