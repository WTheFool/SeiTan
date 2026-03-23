import unittest
import sys
import os
import time
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.db import init_db, cursor, conn
from systems.cycle_engine import start_cycle, record_response, process_cycle, ensure_state

class TestCycleEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    def setUp(self):
        cursor.execute("DELETE FROM cycle_state")
        conn.commit()

    def test_ensure_state(self):
        ensure_state(1, 1)
        cursor.execute("SELECT pending FROM cycle_state WHERE user_id=1 AND guild_id=1")
        row = cursor.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], 0) # Default is 0

    def test_start_cycle(self):
        start_cycle(1, 1)
        cursor.execute("SELECT pending, last_ping FROM cycle_state WHERE user_id=1 AND guild_id=1")
        row = cursor.fetchone()
        self.assertEqual(row[0], 1)
        self.assertIsNotNone(row[1])

    def test_record_response(self):
        start_cycle(1, 1)
        record_response(1, 1)
        cursor.execute("SELECT pending, last_response FROM cycle_state WHERE user_id=1 AND guild_id=1")
        row = cursor.fetchone()
        self.assertEqual(row[0], 0)
        self.assertIsNotNone(row[1])

    def test_process_cycle_success(self):
        user_id = 2
        guild_id = 2
        
        # Manually construct a successful cycle (response within 30 min)
        ensure_state(user_id, guild_id)
        now = datetime.utcnow()
        ping_time = now - timedelta(minutes=10)
        resp_time = now - timedelta(minutes=5)
        
        cursor.execute("""
        UPDATE cycle_state
        SET last_ping=?, last_response=?, pending=1, current_streak=0, max_streak=0
        WHERE user_id=? AND guild_id=?
        """, (str(ping_time), str(resp_time), user_id, guild_id))
        conn.commit()
        
        result = process_cycle(user_id, guild_id, "default")
        self.assertEqual(result, "success")
        
        cursor.execute("SELECT pending, current_streak, max_streak FROM cycle_state WHERE user_id=? AND guild_id=?", (user_id, guild_id))
        row = cursor.fetchone()
        self.assertEqual(row[0], 0) # pending cleared
        self.assertEqual(row[1], 1) # streak increased
        self.assertEqual(row[2], 1) # max streak updated

    def test_process_cycle_fail(self):
        user_id = 3
        guild_id = 3
        
        # Manually construct a failed cycle (response took too long)
        ensure_state(user_id, guild_id)
        now = datetime.utcnow()
        ping_time = now - timedelta(minutes=40)
        resp_time = now - timedelta(minutes=5) # Responded 35 mins later
        
        cursor.execute("""
        UPDATE cycle_state
        SET last_ping=?, last_response=?, pending=1, missed_days=0
        WHERE user_id=? AND guild_id=?
        """, (str(ping_time), str(resp_time), user_id, guild_id))
        conn.commit()
        
        result = process_cycle(user_id, guild_id, "default")
        self.assertEqual(result, "fail")
        
        cursor.execute("SELECT missed_days FROM cycle_state WHERE user_id=? AND guild_id=?", (user_id, guild_id))
        row = cursor.fetchone()
        self.assertEqual(row[0], 0) # default mode doesn't increment missed days

    def test_process_cycle_fail_incremental(self):
        user_id = 4
        guild_id = 4
        
        # Failed cycle with incremental mode
        ensure_state(user_id, guild_id)
        now = datetime.utcnow()
        ping_time = now - timedelta(minutes=60)
        
        # No response at all
        cursor.execute("""
        UPDATE cycle_state
        SET last_ping=?, last_response=NULL, pending=1, missed_days=0
        WHERE user_id=? AND guild_id=?
        """, (str(ping_time), user_id, guild_id))
        conn.commit()
        
        result = process_cycle(user_id, guild_id, "incremental")
        self.assertEqual(result, "fail")
        
        cursor.execute("SELECT missed_days FROM cycle_state WHERE user_id=? AND guild_id=?", (user_id, guild_id))
        row = cursor.fetchone()
        self.assertEqual(row[0], 1) # Incremental mode adds 1 to missed days

if __name__ == '__main__':
    unittest.main()
