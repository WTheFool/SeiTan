import unittest
import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.db import init_db, cursor, conn
from database.db_methods import SentencesDB, SettingsDB, CooldownDB
from systems.sentence_logic import apply_sentence_effect

class TestSentenceLogic(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    def setUp(self):
        cursor.execute("DELETE FROM sentences")
        cursor.execute("DELETE FROM guild_settings")
        cursor.execute("DELETE FROM global_cooldowns")
        conn.commit()

    def test_apply_sentence_success_default_local(self):
        user_id = 1
        guild_id = 1
        # Insert a 10-day local sentence
        cursor.execute("INSERT INTO sentences (user_id, guild_id, days_left, original_days, mode) VALUES (?, ?, ?, ?, ?)", (user_id, guild_id, 10, 10, "default"))
        conn.commit()
        
        apply_sentence_effect(user_id, guild_id, "default", "success")
        
        row = SentencesDB.get_sentence(user_id, guild_id)
        self.assertEqual(row[0], 9) # 1 day subtracted

    def test_apply_sentence_fail_default(self):
        user_id = 2
        guild_id = 2
        cursor.execute("INSERT INTO sentences (user_id, guild_id, days_left, original_days, mode) VALUES (?, ?, ?, ?, ?)", (user_id, guild_id, 10, 10, "default"))
        conn.commit()
        
        apply_sentence_effect(user_id, guild_id, "default", "fail")
        
        row = SentencesDB.get_sentence(user_id, guild_id)
        self.assertEqual(row[0], 10) # No change on fail for default

    def test_apply_sentence_fail_incremental(self):
        user_id = 3
        guild_id = 3
        cursor.execute("INSERT INTO sentences (user_id, guild_id, days_left, original_days, mode) VALUES (?, ?, ?, ?, ?)", (user_id, guild_id, 10, 10, "incremental"))
        conn.commit()
        
        apply_sentence_effect(user_id, guild_id, "incremental", "fail")
        
        row = SentencesDB.get_sentence(user_id, guild_id)
        self.assertEqual(row[0], 11) # +1 day on fail for incremental

    def test_apply_sentence_fail_consecutive(self):
        user_id = 4
        guild_id = 4
        # Sentence started at 10, they got it down to 5
        cursor.execute("INSERT INTO sentences (user_id, guild_id, days_left, original_days, mode) VALUES (?, ?, ?, ?, ?)", (user_id, guild_id, 5, 10, "consecutive"))
        conn.commit()
        
        apply_sentence_effect(user_id, guild_id, "consecutive", "fail")
        
        row = SentencesDB.get_sentence(user_id, guild_id)
        self.assertEqual(row[0], 10) # Reset back to original_days (10)

    def test_apply_sentence_success_global_hell(self):
        user_id = 5
        guild_id_1 = 50
        guild_id_2 = 60
        
        # Setup Global Hell
        SettingsDB.set_global_hell(guild_id_1, 1)
        SettingsDB.set_global_hell(guild_id_2, 1)
        
        # Insert sentence in both global servers
        cursor.execute("INSERT INTO sentences (user_id, guild_id, days_left, original_days, mode) VALUES (?, ?, ?, ?, ?)", (user_id, guild_id_1, 10, 10, "default"))
        cursor.execute("INSERT INTO sentences (user_id, guild_id, days_left, original_days, mode) VALUES (?, ?, ?, ?, ?)", (user_id, guild_id_2, 10, 10, "default"))
        conn.commit()
        
        # User correctly answers in Server 1
        apply_sentence_effect(user_id, guild_id_1, "default", "success")
        
        # Verify it dropped to 9 in Server 1
        row1 = SentencesDB.get_sentence(user_id, guild_id_1)
        self.assertEqual(row1[0], 9)
        
        # Verify it ALSO dropped to 9 in Server 2 (because of global sync)
        row2 = SentencesDB.get_sentence(user_id, guild_id_2)
        self.assertEqual(row2[0], 9)
        
        # User tries to answer in Server 2 immediately after (trying to double dip)
        apply_sentence_effect(user_id, guild_id_2, "default", "success")
        
        # Should still be 9 because of the 24 hour cooldown
        row2_post = SentencesDB.get_sentence(user_id, guild_id_2)
        self.assertEqual(row2_post[0], 9)
        
    def test_prevent_negative_days(self):
        user_id = 6
        guild_id = 6
        
        # Edge case: somehow reaching 0 and succeeding again
        cursor.execute("INSERT INTO sentences (user_id, guild_id, days_left, original_days, mode) VALUES (?, ?, ?, ?, ?)", (user_id, guild_id, 0, 10, "default"))
        conn.commit()
        
        apply_sentence_effect(user_id, guild_id, "default", "success")
        
        row = SentencesDB.get_sentence(user_id, guild_id)
        self.assertEqual(row[0], 0) # Shouldn't go to -1

if __name__ == '__main__':
    unittest.main()
