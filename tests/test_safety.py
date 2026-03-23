import unittest
import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from systems.safety import check_cooldown, command_cooldowns

class TestSafety(unittest.TestCase):

    def setUp(self):
        command_cooldowns.clear()

    def test_check_cooldown(self):
        user_id = 1
        
        # First call should succeed
        self.assertTrue(check_cooldown(user_id, seconds=2))
        
        # Immediate second call should fail
        self.assertFalse(check_cooldown(user_id, seconds=2))
        
        # Wait 2.1 seconds
        time.sleep(2.1)
        
        # Should succeed again
        self.assertTrue(check_cooldown(user_id, seconds=2))

if __name__ == '__main__':
    unittest.main()
