#!/usr/bin/python3

import unittest

from nydus.common.validity import *

class TestValidIPaddr(unittest.TestCase):

    def test_simple(self):
        self.assertTrue(is_valid_ipaddr("192.168.1.1"))

    def test_crutech(self):
        self.assertTrue(is_valid_ipaddr("192.168.67.253"))

    def test_min(self):
        self.assertTrue(is_valid_ipaddr("0.0.0.0"))

    def test_max(self):
        self.assertTrue(is_valid_ipaddr("255.255.255.255"))

    def test_under1(self):
        self.assertFalse(is_valid_ipaddr("-1.4.16.200"))

    def test_under2(self):
        self.assertFalse(is_valid_ipaddr("1.-4.16.200"))

    def test_under3(self):
        self.assertFalse(is_valid_ipaddr("1.4.-16.200"))

    def test_under4(self):
        self.assertFalse(is_valid_ipaddr("1.4.16.-200"))

    def test_over1(self):
        self.assertFalse(is_valid_ipaddr("256.13.144.69"))

    def test_over2(self):
        self.assertFalse(is_valid_ipaddr("10.999.144.69"))

    def test_over3(self):
        self.assertFalse(is_valid_ipaddr("10.13.1044.69"))

    def test_over4(self):
        self.assertFalse(is_valid_ipaddr("10.13.144.652"))

    def test_short(self):
        self.assertFalse(is_valid_ipaddr("155.253.67"))

    def test_long(self):
        self.assertFalse(is_valid_ipaddr("155.253.67.90.216"))

    def test_alph1(self):
        self.assertFalse(is_valid_ipaddr("a5.155.253.67"))

    def test_alph2(self):
        self.assertFalse(is_valid_ipaddr("5.1YY.253.67"))

    def test_alph3(self):
        self.assertFalse(is_valid_ipaddr("5.155.5e3.67"))

    def test_alph4(self):
        self.assertFalse(is_valid_ipaddr("5.155.253.6P"))

    def test_alph(self):
        self.assertFalse(is_valid_ipaddr("A2.b3.4F.L9"))

    def test_nodots(self):
        self.assertFalse(is_valid_ipaddr("1019914469"))


class TestValidPort(unittest.TestCase):
    
    def test_min(self):
        self.assertTrue(is_valid_port("0"))

    def test_max(self):
        self.assertTrue(is_valid_port(str(2**16 - 1)))

    def test_intmin(self):
        self.assertFalse(is_valid_port(0))

    def test_intmax(self):
        self.assertFalse(is_valid_port(2**16 - 1))

    def test_under(self):
        self.assertFalse(is_valid_port("-1"))

    def test_over(self):
        self.assertFalse(is_valid_port(str(2**16)))

    def test_admin(self):
        self.assertTrue(is_valid_port("1024"))

    def test_ssh(self):
        self.assertTrue(is_valid_port("22"))

    def test_nydus(self):
        self.assertTrue(is_valid_port("2011"))

    def test_type1(self):
        self.assertFalse(is_valid_port(8036))

    def test_type2(self):
        self.assertFalse(is_valid_port(True))

    def test_type3(self):
        self.assertFalse(is_valid_port(["2011"]))

    def test_type4(self):
        self.assertFalse(is_valid_port(78.0))


class TestInteger(unittest.TestCase):

    def test_pos(self):
        self.assertTrue(is_integer("12345"))

    def test_neg(self):
        self.assertTrue(is_integer("-9582"))

    def test_zero(self):
        self.assertTrue(is_integer("0"))

    def test_int(self):
        self.assertFalse(is_integer(459))

    def test_bool(self):
        self.assertFalse(is_integer(True))

    def test_list(self):
        self.assertFalse(is_integer(["23", "45"]))

    def test_float(self):
        self.assertFalse(is_integer(9554.00))


class TestPosInteger(unittest.TestCase):

    def test_pos(self):
        self.assertTrue(is_positive_integer("12345"))

    def test_neg(self):
        self.assertFalse(is_positive_integer("-9582"))

    def test_one(self):
        self.assertTrue(is_positive_integer("1"))

    def test_minusone(self):
        self.assertFalse(is_positive_integer("-1"))

    def test_zero(self):
        self.assertFalse(is_positive_integer("0"))

    def test_int(self):
        self.assertFalse(is_positive_integer(459))

    def test_bool(self):
        self.assertFalse(is_positive_integer(True))

    def test_list(self):
        self.assertFalse(is_positive_integer(["23", "45"]))

    def test_float(self):
        self.assertFalse(is_positive_integer(9554.00))


class TestNonNegInteger(unittest.TestCase):

    def test_pos(self):
        self.assertTrue(is_nonnegative_integer("12345"))

    def test_neg(self):
        self.assertFalse(is_nonnegative_integer("-9582"))

    def test_one(self):
        self.assertTrue(is_nonnegative_integer("1"))

    def test_minusone(self):
        self.assertFalse(is_nonnegative_integer("-1"))

    def test_zero(self):
        self.assertTrue(is_nonnegative_integer("0"))

    def test_int(self):
        self.assertFalse(is_nonnegative_integer(459))

    def test_bool(self):
        self.assertFalse(is_nonnegative_integer(True))

    def test_list(self):
        self.assertFalse(is_nonnegative_integer(["23", "45"]))

    def test_float(self):
        self.assertFalse(is_nonnegative_integer(9554.00))


class TestLimitedInteger(unittest.TestCase):

    def test_mid(self):
        self.assertTrue(is_limited_integer("5", 1, 10))

    def test_bot(self):
        self.assertTrue(is_limited_integer("1", 1, 10))

    def test_top(self):
        self.assertTrue(is_limited_integer("10", 1, 10))

    def test_over(self):
        self.assertFalse(is_limited_integer("11", 1, 10))

    def test_under(self):
        self.assertFalse(is_limited_integer("0", 1, 10))

    def test_neg_mid(self):
        self.assertTrue(is_limited_integer("-20", -35, -11))

    def test_neg_bot(self):
        self.assertTrue(is_limited_integer("-35", -35, -11))

    def test_neg_top(self):
        self.assertTrue(is_limited_integer("-11", -35, -11))

    def test_neg_over(self):
        self.assertFalse(is_limited_integer("-10", -35, -11))

    def test_neg_under(self):
        self.assertFalse(is_limited_integer("-36", -35, -11))

    def test_wide_pos(self):
        self.assertTrue(is_limited_integer("350", -1200, 1820))

    def test_wide_neg(self):
        self.assertTrue(is_limited_integer("-950", -1200, 1820))

    def test_wide_mid(self):
        self.assertTrue(is_limited_integer("310", -1200, 1820))

    def test_wide_zero(self):
        self.assertTrue(is_limited_integer("0", -1200, 1820))

    def test_wide_over(self):
        self.assertFalse(is_limited_integer("1821", -1200, 1820))

    def test_wide_under(self):
        self.assertFalse(is_limited_integer("-1201", -1200, 1820))

    def test_wide_farover(self):
        self.assertFalse(is_limited_integer("3218", -1200, 1820))

    def test_wide_farunder(self):
        self.assertFalse(is_limited_integer("-1786", -1200, 1820))

    def test_minval1(self):
        with self.assertRaises(AssertionError):
            is_limited_integer("5", True, 10)

    def test_minval1(self):
        with self.assertRaises(AssertionError):
            is_limited_integer("5", "1", 10)

    def test_maxval1(self):
        with self.assertRaises(AssertionError):
            is_limited_integer("5", 1, 10.0)

    def test_maxval1(self):
        with self.assertRaises(AssertionError):
            is_limited_integer("5", 1, "10")

    def test_unrange1(self):
        with self.assertRaises(AssertionError):
            is_limited_integer("14", 20, 10)

    def test_unrange2(self):
        with self.assertRaises(AssertionError):
            is_limited_integer("-50", -23, -64)

    def test_norange1(self):
        self.assertTrue(is_limited_integer("0", 0, 0))

    def test_norange2(self):
        self.assertTrue(is_limited_integer("57", 57, 57))

    def test_norange3(self):
        self.assertTrue(is_limited_integer("-13", -13, -13))

    def test_int(self):
        self.assertFalse(is_limited_integer(19, 1, 52))

    def test_bool(self):
        self.assertFalse(is_limited_integer(False, -1, 1))

    def test_list(self):
        self.assertFalse(is_limited_integer(["88434", "11111"], 3, 4))

    def test_float(self):
        self.assertFalse(is_limited_integer(9248.00, 9000, 10000))


class TestVersion(unittest.TestCase):

    def test_two(self):
        self.assertTrue(is_valid_version("1.0", 2))

    def test_three(self):
        self.assertTrue(is_valid_version("1.0.0", 3))

    def test_four(self):
        self.assertTrue(is_valid_version("1.0.0.0", 4))

    def test_five(self):
        self.assertTrue(is_valid_version("1.0.0.0.0", 5))

    def test_complex(self):
        self.assertTrue(is_valid_version("2.18.9", 3))

    def test_neg(self):
        self.assertFalse(is_valid_version("-1.0.0", 3))

    def test_empty_one(self):
        self.assertFalse(is_valid_version(".1.0", 3))

    def test_empty_two(self):
        self.assertFalse(is_valid_version("2..5", 3))

    def test_empty_three(self):
        self.assertFalse(is_valid_version("1.3.", 3))


class TestMinecraftVersion(unittest.TestCase):

    def test_simple1(self):
        self.assertTrue(is_valid_minecraft_version("1.20.4"))

    def test_simple2(self):
        self.assertTrue(is_valid_minecraft_version("1.20.6"))

    def test_simple3(self):
        self.assertTrue(is_valid_minecraft_version("1.21.4"))

    def test_opti1(self):
        self.assertTrue(is_valid_minecraft_version("1.20.4-OptiFine_HD_U_I7"))

    def test_opti2(self):
        self.assertTrue(is_valid_minecraft_version("1.21.3-OptiFine_HD_U_J2"))

    def test_rc1(self):
        self.assertTrue(is_valid_minecraft_version("1.21-rc1"))

    def test_rc2(self):
        self.assertTrue(is_valid_minecraft_version("1.21.4-rc3"))

    def test_rc2(self):
        self.assertTrue(is_valid_minecraft_version("1.20-rc1"))

    def test_pre1(self):
        self.assertTrue(is_valid_minecraft_version("1.21.4-pre2"))

    def test_pre2(self):
        self.assertTrue(is_valid_minecraft_version("1.20.3-pre4"))

    def test_pre3(self):
        self.assertTrue(is_valid_minecraft_version("1.20-pre6"))

class TestMineUname(unittest.TestCase):

    def test_simple1(self):
        self.assertTrue(is_valid_minecraft_username("CrutechAccount2"))

    def test_simple2(self):
        self.assertTrue(is_valid_minecraft_username("CrutechAccount10"))

    def test_simple1(self):
        self.assertTrue(is_valid_minecraft_username("xx_Iamdabest_xx"))

    def test_empty(self):
        self.assertFalse(is_valid_minecraft_username(""))


class TestMineUUID(unittest.TestCase):

    def test_simple1(self):
        self.assertTrue(is_valid_minecraft_uuid("646569dcac574eea88f2983856e505e4"))

    def test_simple2(self):
        self.assertTrue(is_valid_minecraft_uuid("b2de15d62a854f679d74342009d6a3c5"))

    def test_simple3(self):
        self.assertTrue(is_valid_minecraft_uuid("302e3c2933524f52b69338cf5d84f5cb"))

    def test_short(self):
        self.assertFalse(is_valid_minecraft_uuid("646569dcac574eea88f2983856e505e"))

    def test_long(self):
        self.assertFalse(is_valid_minecraft_uuid("b2de15d62a854f679d74342009d6a3c51"))

    def test_letter1(self):
        self.assertFalse(is_valid_minecraft_uuid("302E3c2933524f52b69338cf5d84f5cb"))

    def test_letter2(self):
        self.assertFalse(is_valid_minecraft_uuid("646569dcac574eea88f2983856g505e4"))

    def test_letter3(self):
        self.assertFalse(is_valid_minecraft_uuid("b2de15x62a854f679d74342009d6a3c5"))

    def test_letter4(self):
        self.assertFalse(is_valid_minecraft_uuid("302p3c2933524q52b69338rs5d84t5uv"))

class TestMSALCID(unittest.TestCase):

    def test_simple1(self):
        self.assertTrue(is_valid_minecraft_token("1.20.4"))

class TestMSALTok(unittest.TestCase):

    def test_simple1(self):
        self.assertTrue(is_nonempty_str("1.20.4"))

class TestXBLTok(unittest.TestCase):

    def test_simple1(self):
        self.assertTrue(is_nonempty_str("1.20.4"))

class TestXSTSTok(unittest.TestCase):

    def test_simple1(self):
        self.assertTrue(is_nonempty_str("1.20.4"))

class TestNonEmpStr(unittest.TestCase):

    def test_simple1(self):
        self.assertTrue(is_nonempty_str("1.20.4"))

    def test_no(self):
        self.assertFalse(is_nonempty_str(""))

    def test_type1(self):
        self.assertFalse(is_nonempty_str(True))

    def test_type2(self):
        self.assertFalse(is_nonempty_str(0.1))

    def test_type3(self):
        self.assertFalse(is_nonempty_str(14))

    def test_type4(self):
        self.assertFalse(is_nonempty_str([]))

if __name__ == "__main__":
    unittest.main()
