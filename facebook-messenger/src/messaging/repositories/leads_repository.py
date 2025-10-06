# facebook-messenger/src/messaging/repositories/leads_repository.py
"""
Lead repository for managing camera leads
Single Responsibility: Lead data persistence and retrieval
Uses Neon PostgreSQL database
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Optional, Any
from datetime import datetime


class LeadsRepository:
    """
    Handles lead-related database operations
    Stores camera matches that need messaging
    """
    
    def __init__(self, connection_string: str = None):
        self.connection_string = connection_string or os.getenv("DATABASE_URL")
        
        if not self.connection_string:
            raise ValueError("DATABASE_URL environment variable not set")
        
        self._ensure_database()
    
    def _get_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.connection_string)
    
    def _ensure_database(self) -> None:
        """Create tables if they don't exist"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    # Create leads table
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS leads (
                            order_id SERIAL PRIMARY KEY,
                            session_id INTEGER NOT NULL,
                            camera_id INTEGER NOT NULL,
                            camera_name TEXT NOT NULL,
                            price DECIMAL(10, 2),
                            url TEXT NOT NULL,
                            title TEXT NOT NULL,
                            confidence DECIMAL(5, 4) NOT NULL,
                            savings DECIMAL(10, 2) DEFAULT 0,
                            status TEXT DEFAULT 'pending',
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            messaged_at TIMESTAMP,
                            error_message TEXT,
                            UNIQUE(session_id, camera_id, url)
                        )
                    """)
                    
                    # Create indexes for faster queries
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_leads_status 
                        ON leads(status)
                    """)
                    
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_leads_session 
                        ON leads(session_id)
                    """)
                    
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_leads_created 
                        ON leads(created_at DESC)
                    """)
                    
                    conn.commit()
                    print("[LeadsRepository] Database tables initialized")
                    
        except Exception as e:
            print(f"[LeadsRepository] Error initializing database: {e}")
            raise
    
    def create_lead(self, lead_data: Dict[str, Any]) -> Optional[int]:
        """
        Create a new lead
        Returns order_id if successful, None if duplicate
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO leads (
                            session_id, camera_id, camera_name, price, 
                            url, title, confidence, savings, status
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING order_id
                    """, (
                        lead_data['session_id'],
                        lead_data['camera_id'],
                        lead_data['camera_name'],
                        lead_data.get('price'),
                        lead_data['url'],
                        lead_data['title'],
                        lead_data['confidence'],
                        lead_data.get('savings', 0),
                        lead_data.get('status', 'pending')
                    ))
                    
                    order_id = cursor.fetchone()[0]
                    conn.commit()
                    
                    print(f"[LeadsRepository] Created lead #{order_id}: {lead_data['camera_name']}")
                    return order_id
                    
        except psycopg2.IntegrityError:
            print(f"[LeadsRepository] Duplicate lead: {lead_data['url']}")
            return None
        except Exception as e:
            print(f"[LeadsRepository] Error creating lead: {e}")
            return None
    
    def get_lead_by_id(self, order_id: int) -> Optional[Dict[str, Any]]:
        """Get lead by order_id"""
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT * FROM leads WHERE order_id = %s
                    """, (order_id,))
                    
                    row = cursor.fetchone()
                    return dict(row) if row else None
                    
        except Exception as e:
            print(f"[LeadsRepository] Error getting lead: {e}")
            return None
    
    def get_pending_leads(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get leads that need messaging"""
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT * FROM leads 
                        WHERE status = 'pending'
                        ORDER BY created_at ASC
                        LIMIT %s
                    """, (limit,))
                    
                    return [dict(row) for row in cursor.fetchall()]
                    
        except Exception as e:
            print(f"[LeadsRepository] Error getting pending leads: {e}")
            return []
    
    def update_lead_status(self, order_id: int, status: str, 
                          error_message: str = None) -> bool:
        """Update lead status"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    if status == 'messaged':
                        cursor.execute("""
                            UPDATE leads 
                            SET status = %s, 
                                updated_at = CURRENT_TIMESTAMP,
                                messaged_at = CURRENT_TIMESTAMP,
                                error_message = %s
                            WHERE order_id = %s
                        """, (status, error_message, order_id))
                    else:
                        cursor.execute("""
                            UPDATE leads 
                            SET status = %s, 
                                updated_at = CURRENT_TIMESTAMP,
                                error_message = %s
                            WHERE order_id = %s
                        """, (status, error_message, order_id))
                    
                    success = cursor.rowcount > 0
                    conn.commit()
                    
                    if success:
                        print(f"[LeadsRepository] Updated lead #{order_id} to '{status}'")
                    
                    return success
                    
        except Exception as e:
            print(f"[LeadsRepository] Error updating lead: {e}")
            return False
    
    def get_leads_by_session(self, session_id: int) -> List[Dict[str, Any]]:
        """Get all leads for a session"""
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT * FROM leads 
                        WHERE session_id = %s
                        ORDER BY created_at DESC
                    """, (session_id,))
                    
                    return [dict(row) for row in cursor.fetchall()]
                    
        except Exception as e:
            print(f"[LeadsRepository] Error getting session leads: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get lead statistics"""
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Overall stats
                    cursor.execute("""
                        SELECT 
                            COUNT(*) as total_leads,
                            SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                            SUM(CASE WHEN status = 'messaged' THEN 1 ELSE 0 END) as messaged,
                            SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as errors,
                            AVG(price) as avg_price,
                            AVG(savings) as avg_savings
                        FROM leads
                    """)
                    
                    stats = dict(cursor.fetchone())
                    
                    # Status breakdown
                    cursor.execute("""
                        SELECT status, COUNT(*) as count
                        FROM leads
                        GROUP BY status
                    """)
                    
                    stats['status_breakdown'] = [dict(row) for row in cursor.fetchall()]
                    
                    return stats
                    
        except Exception as e:
            print(f"[LeadsRepository] Error getting statistics: {e}")
            return {}
    
    def cleanup_old_leads(self, days: int = 30) -> int:
        """Clean up old completed leads"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        DELETE FROM leads 
                        WHERE status IN ('messaged', 'purchased', 'delivered')
                        AND created_at < CURRENT_TIMESTAMP - INTERVAL '%s days'
                    """, (days,))
                    
                    deleted = cursor.rowcount
                    conn.commit()
                    
                    print(f"[LeadsRepository] Cleaned up {deleted} old leads")
                    return deleted
                    
        except Exception as e:
            print(f"[LeadsRepository] Error cleaning up leads: {e}")
            return 0