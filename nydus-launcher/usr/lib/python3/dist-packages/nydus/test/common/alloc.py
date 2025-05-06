#!/usr/bin/python3

import unittest
import os

from nydus.common.alloc_utils import *
from nydus.common.allocater import *

class TestView(unittest.TestCase):

    def setUp(self):
        self.allocfile = "/tmp/nydus-alloc.csv"

        with open(self.allocfile, "w") as f:
            f.write("")
            f.flush()

        self.header = "client_ip,client_username,alloc_time,ms_username,msal_token,msal_expiry,xboxlive_token,xboxlive_expiry,xsts_token,xsts_expiry,xsts_hash,mc_token,mc_expiry,mc_username,mc_uuid"

    def tearDown(self):
        os.remove(self.allocfile)

    def test_view(self):

        allocengine = AllocEngine(self.allocfile)

        out = str(allocengine)
        expected_out = self.header + "\n"

        self.assertEqual(out, expected_out)

if __name__ == "__main__":
    unittest.main()
