import os
import sys
import json
import unittest

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import guardian
import guardian_db

class TestKeylessProxy(unittest.TestCase):
    def setUp(self):
        # Backup existing config
        self.config_path = os.path.join(os.path.dirname(__file__), "config.json")
        self.config_backup = None
        if os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config_backup = f.read()
                
    def tearDown(self):
        # Restore existing config
        if self.config_backup is not None:
            with open(self.config_path, "w", encoding="utf-8") as f:
                f.write(self.config_backup)

    def test_quota_check_proxy(self):
        # Simulate unauthenticated state with no key
        config = {
            "github_username": "test_user",
            "ntfy_topic": "test_topic",
            "tracked_tasks": ["dsa"],
            "gemini_api_key": ""
        }
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
            
        # Check quota status when unauthenticated and no key
        status, detail = guardian.check_gemini_quota_status("")
        self.assertEqual(status, "no_key")
        
        # Simulate logged in state under Gmail
        config["google_auth_email"] = "aditya.dev06@gmail.com"
        config["google_auth_name"] = "Aditya Dev06"
        config["google_auth_token"] = "ya29.mock_token_success"
        
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
            
        # Check quota status now - should resolve using premium proxy key (which is active)
        status, detail = guardian.check_gemini_quota_status("")
        self.assertIn(status, ["available", "exhausted"])
        print(f"Proxy check succeeded: status={status}, detail={detail}")

if __name__ == "__main__":
    unittest.main()
