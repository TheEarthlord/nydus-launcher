#!/usr/bin/python3

import unittest
import os
import datetime

from nydus.common.netauth import *

class TestXboxTimestamp(unittest.TestCase):

    def test_simple1(self):
        in_ts = "2025-05-13T18:13:40.5822307Z"
        out_ts = "2025-05-13T18:13:40.582230Z"

        dt = parse_xbox_timestamp(in_ts)

        self.assertTrue(isinstance(dt, datetime.datetime))
        self.assertEqual(out_ts, str(dt) + "Z")

    def test_simple2(self):
        in_ts = "2025-05-13T18:13:40.582230Z"
        out_ts = "2025-05-13T18:13:40.582230Z"

        dt = parse_xbox_timestamp(in_ts)

        self.assertTrue(isinstance(dt, datetime.datetime))
        self.assertEqual(out_ts, str(dt) + "Z")

    def test_simple3(self):
        in_ts = "2025-05-13T18:13:40.002230Z"
        out_ts = "2025-05-13T18:13:40.002230Z"

        dt = parse_xbox_timestamp(in_ts)

        self.assertTrue(isinstance(dt, datetime.datetime))
        self.assertEqual(out_ts, str(dt) + "Z")

    def test_simple4(self):
        in_ts = "2025-05-13T18:13:40.0022305Z"
        out_ts = "2025-05-13T18:13:40.002230Z"

        dt = parse_xbox_timestamp(in_ts)

        self.assertTrue(isinstance(dt, datetime.datetime))
        self.assertEqual(out_ts, str(dt) + "Z")


if __name__ == "__main__":
    unittest.main()
