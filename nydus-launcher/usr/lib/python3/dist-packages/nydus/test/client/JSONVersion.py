#!/usr/bin/python3

from nydus.client.JSONVersion import *

class TestResolveRule(unittest.TestCase):

    def test_linux_yes(self):
        rules = [
            {
                "action": "allow",
                "os": {
                    "name": "linux"
                }
            }
        ]

        self.assertTrue(JSONVersion.resolve_rule(rules))

    def test_mac_no(self):
        rules = [
            {
                "action": "allow",
                "os": {
                    "name": "osx"
                }
            }
        ]
        self.assertFalse(JSONVersion.resolve_rule(rules))

    def test_windows_no(self):
        rules = [
            {
                "action": "allow",
                "os": {
                    "name": "windows"
                }
            }
        ]

        self.assertFalse(JSONVersion.resolve_rule(rules))

    def test_x86_yes(self):
        rules = [
            {
                "action": "allow",
                "os": {
                    "arch": "x86"
                }
            }
        ]
        self.assertTrue(JSONVersion.resolve_rule(rules))

if __name__ == "__main__":
    unittest.main()
