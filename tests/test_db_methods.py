import unittest
import sqlite3
import os
import time
import sys

# Add the project root to sys.path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.db_methods import SettingsDB, SentencesDB, CooldownDB
from database.db import init_db, cursor, conn

class TestDBMethods(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # We will use an in-memory database or a test file for testing
        # But since the db module automatically connects to config.DB_PATH,
        # we will just initialize it and clear tables before each test.
        init_db()

    def setUp(self):
        # Clear the tables before each test to ensure isolation
        cursor.execute("DELETE FROM guild_settings")
        cursor.execute("DELETE FROM sentences")
        cursor.execute("DELETE FROM appeal_cooldowns")
        cursor.execute("DELETE FROM global_cooldowns")
        conn.commit()

    def test_settings_db_global_hell(self):
        guild_id = 12345
        
        # Default should be false (0) or not exist
        self.assertFalse(SettingsDB.is_global_hell(guild_id))
        
        # Enable it
        SettingsDB.set_global_hell(guild_id, 1)
        self.assertTrue(SettingsDB.is_global_hell(guild_id))
        
        # Disable it
        SettingsDB.set_global_hell(guild_id, 0)
        self.assertFalse(SettingsDB.is_global_hell(guild_id))

    def test_sentences_db_crud(self):
        user_id = 999
        guild_id = 12345
        days = 10
        mode = "incremental"
        
        # Insert a sentence manually to test retrieval
        from datetime import datetime
        cursor.execute("""
        INSERT INTO sentences (user_id, guild_id, days_left, original_days, mode, last_check)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, guild_id, days, days, mode, str(datetime.utcnow())))
        conn.commit()
        
        # Test retrieval
        data = SentencesDB.get_sentence(user_id, guild_id)
        self.assertIsNotNone(data)
        self.assertEqual(data[0], 10)  # days_left
        self.assertEqual(data[1], 10)  # original_days
        self.assertEqual(data[2], "incremental")  # mode
        
        # Test fetching all active
        active = SentencesDB.get_all_active_sentences()
        self.assertEqual(len(active), 1)
        
        # Test update (local)
        SentencesDB.update_days(user_id, guild_id, 5, global_update=False)
        updated = SentencesDB.get_sentence(user_id, guild_id)
        self.assertEqual(updated[0], 5)
        
        # Test delete
        SentencesDB.delete_sentence(user_id, guild_id, global_update=False)
        self.assertIsNone(SentencesDB.get_sentence(user_id, guild_id))

    def test_cooldown_db(self):
        user_id = 999
        now = time.time()
        
        # Set cooldown
        CooldownDB.set_appeal_cooldown(user_id, now)
        fetched = CooldownDB.get_appeal_cooldown(user_id)
        self.assertIsNotNone(fetched)
        self.assertAlmostEqual(fetched, now, places=2)
        
        # Reset cooldown
        CooldownDB.reset_appeal_cooldown(user_id)
        self.assertIsNone(CooldownDB.get_appeal_cooldown(user_id))

if __name__ == '__main__':
    unittest.main()
