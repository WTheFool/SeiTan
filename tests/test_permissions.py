import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.db import init_db, cursor, conn
from systems.permissions import is_sinner_anywhere

class TestPermissions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    def setUp(self):
        cursor.execute("DELETE FROM sentences")
        conn.commit()

    def test_is_sinner_anywhere(self):
        user_id = 99
        guild_id = 1
        
        # Initially not a sinner
        self.assertFalse(is_sinner_anywhere(user_id))
        
        # Add sentence
        cursor.execute("INSERT INTO sentences (user_id, guild_id, days_left, original_days, mode) VALUES (?, ?, ?, ?, ?)", (user_id, guild_id, 10, 10, "default"))
        conn.commit()
        
        # Should now be true
        self.assertTrue(is_sinner_anywhere(user_id))
        
        # Clean up
        cursor.execute("DELETE FROM sentences WHERE user_id=?", (user_id,))
        conn.commit()
        self.assertFalse(is_sinner_anywhere(user_id))

if __name__ == '__main__':
    unittest.main()
