import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.db import init_db, cursor, conn
from systems.phrase_engine import get_phrases, add_phrase, remove_phrase, validate_phrase

class TestPhraseEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    def setUp(self):
        cursor.execute("DELETE FROM phrase_rules")
        conn.commit()

    def test_default_phrase(self):
        guild_id = 999
        phrases = get_phrases(guild_id)
        self.assertEqual(phrases, ["I'm sorry!"])

    def test_add_and_remove_phrase(self):
        guild_id = 999
        add_phrase(guild_id, "I repent", 1)
        
        phrases = get_phrases(guild_id)
        self.assertIn("I repent", phrases)
        
        remove_phrase(guild_id, "I repent")
        phrases = get_phrases(guild_id)
        self.assertEqual(phrases, ["I'm sorry!"])

    def test_validate_phrase(self):
        guild_id = 999
        
        # Test Default
        self.assertTrue(validate_phrase(guild_id, "I'm sorry!"))
        self.assertTrue(validate_phrase(guild_id, "  i'm sorry!  ")) # case insensitive + whitespace
        self.assertFalse(validate_phrase(guild_id, "I'm sorry")) # missing exclamation
        self.assertFalse(validate_phrase(guild_id, "I apologize"))
        
        # Test Custom
        add_phrase(guild_id, "Forgive me SeiTan", 1)
        self.assertTrue(validate_phrase(guild_id, "forgive me seitan"))

if __name__ == '__main__':
    unittest.main()
