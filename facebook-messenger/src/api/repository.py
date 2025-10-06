# facebook-messenger/src/api/repository.py
"""
Lead repository - Single Responsibility: Database operations for leads
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
from typing import List, Dict, Optional


class LeadRepository:
    """Handles lead database operations"""
    
    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL")
        if not self.db_url:
            raise ValueError("DATABASE_URL required")
        self._ensure_table()
    
    def _get_conn(self):
        return psycopg2.connect(self.db_url)
    
    def _ensure_table(self):
        """Create leads table if not exists"""
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS leads (
                        order_id SERIAL PRIMARY KEY,
                        session_id INTEGER NOT NULL,
                        camera_id INTEGER NOT NULL,
                        camera_name TEXT NOT NULL,
                        price DECIMAL(10,2),
                        url TEXT NOT NULL,
                        title TEXT NOT NULL,
                        confidence DECIMAL(5,4) NOT NULL,
                        savings DECIMAL(10,2) DEFAULT 0,
                        status TEXT DEFAULT 'pending',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        messaged_at TIMESTAMP,
                        UNIQUE(url)
                    );
                    CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
                """)
                conn.commit()
    
    def create(self, data: Dict) -> Optional[int]:
        """Create single lead, return order_id or None if duplicate"""
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO leads (session_id, camera_id, camera_name, 
                                         price, url, title, confidence, savings)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING order_id
                    """, (data['session_id'], data['camera_id'], data['camera_name'],
                          data.get('price'), data['url'], data['title'], 
                          data['confidence'], data.get('savings', 0)))
                    return cur.fetchone()[0]
        except psycopg2.IntegrityError:
            return None
    
    def create_batch(self, leads: List[Dict]) -> Dict[str, int]:
        """Create multiple leads efficiently, return counts"""
        created = 0
        duplicates = 0
        
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                for lead in leads:
                    try:
                        cur.execute("""
                            INSERT INTO leads (session_id, camera_id, camera_name,
                                             price, url, title, confidence, savings)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """, (lead['session_id'], lead['camera_id'], lead['camera_name'],
                              lead.get('price'), lead['url'], lead['title'],
                              lead['confidence'], lead.get('savings', 0)))
                        created += 1
                    except psycopg2.IntegrityError:
                        duplicates += 1
                        conn.rollback()  # Rollback this insert, continue with others
                
                conn.commit()
        
        return {"created": created, "duplicates": duplicates}
    
    def get_pending(self, limit: int = 10) -> List[Dict]:
        """Get pending leads"""
        with self._get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM leads 
                    WHERE status = 'pending' 
                    ORDER BY created_at ASC 
                    LIMIT %s
                """, (limit,))
                return [dict(r) for r in cur.fetchall()]
    
    def update_status(self, order_id: int, status: str) -> bool:
        """Update lead status"""
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                if status == 'messaged':
                    cur.execute("""
                        UPDATE leads 
                        SET status = %s, messaged_at = CURRENT_TIMESTAMP 
                        WHERE order_id = %s
                    """, (status, order_id))
                else:
                    cur.execute("""
                        UPDATE leads 
                        SET status = %s 
                        WHERE order_id = %s
                    """, (status, order_id))
                return cur.rowcount > 0