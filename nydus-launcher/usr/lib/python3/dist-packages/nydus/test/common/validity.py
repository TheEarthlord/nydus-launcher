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

class TestMineTok(unittest.TestCase):

    def test_simple1(self):
        self.assertTrue(is_valid_minecraft_token("aaaa"))

class TestMSALCID(unittest.TestCase):

    def test_simple1(self):
        self.assertTrue(is_valid_msal_cid("1ab23456-7890-1c2d-e3fg-45h6789ijk01"))

class TestMSALTok(unittest.TestCase):

    def test_simple1(self):
        self.assertTrue(is_valid_msal_token("EwDoA+pvCAAUKods63Xs1fGlwiccILJ+qE1hANsAAWAREf/CjhHpPXrUmcvXd5P4LzTPisbFoRcYDa8qGgDc/KKXQ52pJ6ZHnOqeZE9UdF70onlB93mEaVniKQm/glzXU5diQd9iDowycq1+lT9NZC9amtGtuHtaT4PjUbP1bztBxJUxamMlv9IsKAhkZPAmK/rVV7TD3mgTikrBSP50q2KHqi5jm5CGeNEYAkT0pZ0gyWulAkdREcO1OxyzEThfgliR8dkJ2BMDU+vj/GcqJZtQ7bsyS5ZPHhCGnvy4H1fUCG/qYWMBVGHsAnKyRXobxlt6KyfnLJdhUkplTfY8jqvTzLfu4FC3rW10O9j15u0YyfNHXjrZ0rp8FR2P9RcQZgAAEGHnBnQ1xsOqRycZ0d1qga6wAulT62/6L4h5wW78aBKuevOYkLWlXUo1n7FOOUN2OnFKD0SErchylB3OBTjLg0pLoK7gQuStnQnSn8jtHfSTjhUMFcGZsJ6NkTYElgKZSRks5EyQ/9iWKeTqsQoKeGVjCjfH4nTp+KbhMYQjZRah6tSm77wxU+qPHh/J3TbtHjKc3PQ9XlEE/T6dMKkuINMvYXwHbNX8Mo3dQlKwtynXw/NdbkqPj66bPyUf8m2+RcDTgzRC3KbOi0DkDekJHI9A4NVavCF1JHyp6i4kMnUCcEsUEkiTNmpSTuwrkbkhdreZOuxvqQ63xunctwMzZ+3BeAYx7HfOwkJRmbrlIWoL4JJRu7y6q5RvcLgVnv2KVXvzDjKkbuHhGs2LWkNzyzv1ipESu7ybRNbcpQpIkRAapg9EmF1Tnw63DuRgBDvXRCvC9x+ij0q+SUTCnr3kS79rCjj/680fgnb/KqN2rMquVkzWP8hvOjiENDijat23Zg4f0/94SYUXuOHWTxgeddQ8FiaIntbR1tEZmgehgAdWdWGru3qgr8huDxEQAU0WvnuGVUTh2TMyA/K7PWPlgU1F7WhrPrFZUprAZs7oW5pdEXL1hbB03ra/e3kFBt2xlD7lRUTDpG+SIMsnSYYIbiBLBD17F9clt0WBdZ4ipIPqP922hSt99u5/QZ4iO44GOhbPDEho7snFkyq8oRCz/MGrsK9y9QHCRXV0Wt6EXnEqnAGx6p0i0Ctj63h3MZcpU+xX6d/NHlLP6HMxfsPS9DaGj0pDHOvH0c0HjDyTk7mWkAqFk6oit3kxDiMt/CYIKzuSwNkY5buzoHrqxee8r/VQko+T0IJEItHDA4OAC5iziL3jWBy5O1hkV6DzKPq+wB71MXmPkpxpL2anYIcYFEQYU5jamHq6Vgt47Z7t185cH+7hAg=="))

    def test_short(self):
        self.assertFalse(is_valid_msal_token("EwDoA+pvCAAUKods63Xs1fGlwiccILJ+qE1hANsAAWAREf/KKXQ52pJ6ZHnOqeZE9UdF70onlB93mEaVniKQm/glzXU5diQd9iDowycq1+lT9NZC9amtGtuHtaT4PjUbP1bztBxJUxamMlv9IsKAhkZPAmK/rVV7TD3mgTikrBSP50q2KHqi5jm5CGeNEYAkT0pZ0gyWulAkdREcO1OxyzEThfgliR8dkJ2BMDU+vj/qYWMBVGHsAnKyRXobxlt6KyfnLJdhUkplTfY8jqvTzLfu4FC3rW10O9j15u0YyfNHXjrZ0rp8FR2P9RcQZgAAEGHnBnQ1xsOqRycZ0d1qga6wAulT62/6L4h5wW78aBKuevOYkLWlXUo1n7FOOUN2OnFKD0SErchylB3OBTjLg0pLoK7gQuStnQnSn8jtHfSTjhUMFcGZsJ6NkTYElgKZSRks5EyQ/9iWKeTqsQoKeGVjCjfH4nTp+KbhMYQjZRah6tSm77wxU+qPHh/T6dMKkuINMvYXwHbNX8Mo3dQlKwtynXw/NdbkqPj66bPyUf8m2+RcDTgzRC3KbOi0DkDekJHI9A4NVavCF1JHyp6i4kMnUCcEsUEkiTNmpSTuwrkbkhdreZOuxvqQ63xunctwMzZ+3BeAYx7HfOwkJRmbrlIWoL4JJRu7y6q5RvcLgVnv2KVXvzDjKkbuHhGs2LWkNzyzv1ipESu7ybRNbcpQpIkRAapg9EmF1Tnw63DuRgBDvXRCvC9x+ij0q+SUTCnr3kS79rCjj/680fgnb/KqN2rMquVkzWP8hvOjiENDijat23Zg4f0/94SYUXuOHWTxgeddQ8FiaIntbR1tEZmgehgAdWdWGru3qgr8huDxEQAU0WvnuGVUTh2TMyA/K7PWPlgU1F7WhrPrFZUprAZs7oW5pdEXL1hbB03ra/e3kFBt2xlD7lRUTDpG+SIMsnSYYIbiBLBD17F9clt0WBdZ4ipIPqP922hSt99u5/QZ4iO44GOhbPDEho7snFkyq8oRCz/MGrsK9y9QHCRXV0Wt6EXnEqnAGx6p0i0Ctj63h3MZcpU+xX6d/NHlLP6HMxfsPS9DaGj0pDHOvH0c0HjDyTk7mWkAqFk6oit3kxDiMt/CYIKzuSwNkY5buzoHrqxee8r/VQko+T0IJEItHDA4OAC5iziL3jWBy5O1hkV6DzKPq+wB71MXmPkpxpL2anYIcYFEQYU5jamHq6Vgt47Z7t185cH+7hAg=="))

    def test_long(self):
        self.assertFalse(is_valid_msal_token("EwDoA+pvCAAUKods63Xs1fGlwiccILJ+qE1hANsAAWAREf/CjhHpPXrUmcvXd5P4LzTPisbFoRcYDa8qGgDc/KKXQ52pJ6ZHnOqeZE9UdF70onlB93mEaVniKQm/glzXU5diQd9iDowycq1+lT9NZC9amtGtuHtaT4PjUbP1bztBxJUxamMlv9IsKAhkZPAmK/rVV7TD3mgTikrBSP50q2KHqi5jm5CGeNEYAkT0pZ0gyWulAkdREcO1OxyzEThfgliR8dkJ2BMDU+vj/KKXQ52pJ6ZHnOqeZE9UdF70onlB93mEaVniKQm/GcqJZtQ7bsyS5ZPHhCGnvy4H1fUCG/qYWMBVGHsAnKyRXobxlt6KyfnLJdhUkplTfY8jqvTzLfu4FC3rW10O9j15u0YyfNHXjrZ0rp8FR2P9RcQZgAAEGHnBnQ1xsOqRycZ0d1qga6wAulT62/6L4h5wW78aBKuevOYkLWlXUo1n7FOOUN2OnFKD0SErchylB3OBTjLg0pLoK7gQuStnQnSn8jtHfSTjhUMFcGZsJ6NkTYElgKZSRks5EyQ/9VQko+T0IJEItHDA4OAC5iziL3jWBy5O1hkV6DzKPq+wB71MXmPkpxpL2anYIcYFEQYU5jamHq6Vgt47Z7t185cH+7hA/giWKeTqsQoKeGVjCjfH4nTp+KbhMYQjZRah6tSm77wxU+qPHh/J3TbtHjKc3PQ9XlEE/QZ4iO44GOhbPDEho7snFkyq8oRC/zT6dMKkuINMvYXwHbNX8Mo3dQlKwtynXw/NdbkqPj66bPyUf8m2+RcDTgzRC3KbOi0DkDekJHI9A4NVavCF1JHyp6i4kMnUCcEsUEkiTNmpSTuwrkbkhdreZOuxvqQ63xunctwMzZ+3BeAYx7HfOwkJRmbrlIWoL4JJRu7y6q5RvcLgVnv2KVXvzDjKkbuHhGs2LWkNzyzv1ipESu7ybRNbcpQpIkRAapg9EmF1Tnw63DuRgBDvXRCvC9x+ij0q+SUTCnr3kS79rCjj/9iWKeTqsQoKeGVjCjfH4nTp+KbhMYQjZRah6tSm77wxU+qPH/h680fgnb/KqN2rMquVkzWP8hvOjiENDijat23Zg4f0/94SYUXuOHWTxgeddQ8FiaIntbR1tEZmgehgAdWdWGru3qgr8huDxEQAU0WvnuGVUTh2TMyA/K7PWPlgU1F7WhrPrFZUprAZs7oW5pdEXL1hbB03ra/e3kFBt2xlD7lRUTDpG+SIMsnSYYIbiBLBD17F9clt0WBdZ4ipIPqP922hSt99u5/QZ4iO44GOhbPDEho7snFkyq8oRCz/MGrsK9y9QHCRXV0Wt6EXnEqnAGx6p0i0Ctj63h3MZcpU+xX6d/NHlLP6HMxfsPS9DaGj0pDHOvH0c0HjDyTk7mWkAqFk6oit3kxDiMt/CYIKzuSwNkY5buzoHrqxee8r/VQko+T0IJEItHDA4OAC5iziL3jWBy5O1hkV6DzKPq+wB71MXmPkpxpL2anYIcYFEQYU5jamHq6Vgt47Z7t185cH+7hAg=="))

    def test_wrong(self):
        self.assertFalse(is_valid_msal_token("EwDoA.pvCAAUKods63Xs1fGlwiccILJ.qE1hANsAAWAREf_CjhHpPXrUmcvXd5P4LzTPisbFoRcYDa8qGgDc_KKXQ52pJ6ZHnOqeZE9UdF70onlB93mEaVniKQm_glzXU5diQd9iDowycq1.lT9NZC9amtGtuHtaT4PjUbP1bztBxJUxamMlv9IsKAhkZPAmK_rVV7TD3mgTikrBSP50q2KHqi5jm5CGeNEYAkT0pZ0gyWulAkdREcO1OxyzEThfgliR8dkJ2BMDU.vj_GcqJZtQ7bsyS5ZPHhCGnvy4H1fUCG_qYWMBVGHsAnKyRXobxlt6KyfnLJdhUkplTfY8jqvTzLfu4FC3rW10O9j15u0YyfNHXjrZ0rp8FR2P9RcQZgAAEGHnBnQ1xsOqRycZ0d1qga6wAulT62_6L4h5wW78aBKuevOYkLWlXUo1n7FOOUN2OnFKD0SErchylB3OBTjLg0pLoK7gQuStnQnSn8jtHfSTjhUMFcGZsJ6NkTYElgKZSRks5EyQ_9iWKeTqsQoKeGVjCjfH4nTp.KbhMYQjZRah6tSm77wxU.qPHh_J3TbtHjKc3PQ9XlEE_T6dMKkuINMvYXwHbNX8Mo3dQlKwtynXw_NdbkqPj66bPyUf8m2.RcDTgzRC3KbOi0DkDekJHI9A4NVavCF1JHyp6i4kMnUCcEsUEkiTNmpSTuwrkbkhdreZOuxvqQ63xunctwMzZ.3BeAYx7HfOwkJRmbrlIWoL4JJRu7y6q5RvcLgVnv2KVXvzDjKkbuHhGs2LWkNzyzv1ipESu7ybRNbcpQpIkRAapg9EmF1Tnw63DuRgBDvXRCvC9x.ij0q.SUTCnr3kS79rCjj_680fgnb_KqN2rMquVkzWP8hvOjiENDijat23Zg4f0_94SYUXuOHWTxgeddQ8FiaIntbR1tEZmgehgAdWdWGru3qgr8huDxEQAU0WvnuGVUTh2TMyA_K7PWPlgU1F7WhrPrFZUprAZs7oW5pdEXL1hbB03ra_e3kFBt2xlD7lRUTDpG.SIMsnSYYIbiBLBD17F9clt0WBdZ4ipIPqP922hSt99u5_QZ4iO44GOhbPDEho7snFkyq8oRCz_MGrsK9y9QHCRXV0Wt6EXnEqnAGx6p0i0Ctj63h3MZcpU.xX6d_NHlLP6HMxfsPS9DaGj0pDHOvH0c0HjDyTk7mWkAqFk6oit3kxDiMt_CYIKzuSwNkY5buzoHrqxee8r_VQko.T0IJEItHDA4OAC5iziL3jWBy5O1hkV6DzKPq.wB71MXmPkpxpL2anYIcYFEQYU5jamHq6Vgt47Z7t185cH.7hAg--"))

class TestXBLTok(unittest.TestCase):

    def test_simple1(self):
        self.assertTrue(is_valid_xboxlive_token("eyJhbGciOiJSU0EtT0FFUCIsImVuYyI6IkExMjhDQkMtSFMyNTYiLCJ6aXAiOiJERUYiLCJ4NXQiOiJxcEQtU2ZoOUg3NFFHOXlMN1hSZXJ5RmZvbk0iLCJjdHkiOiJKV1QifQ.bQnxbQgQ9EF55A5d6X3R-D0sCUjRlzkM9VpLW3Yc3gOc85-Kc5E33Et8r-2NPr7Rc4vrGyYGB5OuyMzAJaZ0IkGHgJQkdjQr5e2lbNUHtWQ_a2KypTzmgA74ehEhPKRQdtiC-R9f8kf23BbEXJIKvjkraRUyNglOMUE3kKESlHQ35al71WDgAXvzGJ3ndEN1a4sK9kX6AjLOjv75huYI2eOtZk3eRlBQDyz-kkEDxgtC0ijPdL41EvBq_NMztD7yNwUA7i3a45OASqhB897vpEZaxBglYfThewDKAICOhkT4G6UJ2LRWjo2HrWnDHDTymzw_jXsUDorqLvGQTJg3DA.nOeKddrwqhpmGng2NWBNbA.Gc_0MiXpwU3MjtjJ2VPrQN_bKB279Ej0Fxnu1YxP0WAu2Qx8LtqEoSwTSWPnDCDLNr9ReOyWEtr_xsu_X1kvqGHjyHOEdPuYdfq-wUltNQdjdrzqp6PRVk9mlmvXnXQJU7Uhyidg0tFmGF5S39YOqCfWhgnDzUIQe-B4aKxkVYcgpEQYXM53A46kre8g9dmO3AxWqVe7-g2GtG59dY906AqcN7tjczAY0C8oQMaus2_m1rcoF1vEnm18_5XyRW-dR-S1S7E0Rt4v8pzLfrDwwdpXR_LhnKce2zCM_UHzkvXnwUKOqns3KcUnip3ibGR51uQ-H_7bN7nwdEBJRufQbHeYtGLkoTuP8B8T7s5QWL84Ijfg9fGbJpC2uqtWljZtNIR1SY_N462PRiMuyE9_ESWkmUUkDykRmPARWkzVkVQNaDich3f3N_QdabCszTwpi62_vwyVAzUSID8-J6sSaReWMRjyrIE6CcYDssafyEfBqRPawfuJYfJRt8vixeXoQhkEQlAl8fhifWa0zm5OXrhB5vP4M-R-NNwyxlxFsYfRf8H46JHiAbFRTMZdzURU9dQEoOmaKJCztRmSlUW4D9Q6XVEdPHS3CCV9H7VHO17_VxHEOegdUdd_vmtYPtbTgGaeJese2gjF9ZAh65T5mddFyYrAl3vSU65BD53gpjEQL3LmRbTIxGBHpnXp2UU96llBp8_Uwr-TzdQOLT8RzfJshssPMHKBLlGNL4ieyvryGK0Du1WL-uvfugI7mD4PReOsnw7E13WMvJhvXelLpvFv43mzFqREmcz2u4upPjfBUgmXpwHKdWTUxLhtsLSn9eOQ8s-2GWqqQKbM2BCRZGcx2RpCHSNJrLGy75D6Y2Yz0HkEB3LpSRz4cZlJEZsDOZpxvLk6tEHD3FFK09alyYJZBuISGtM4mMNbMqkSeh4aA2pHvpVCP_ef0p5HKPx-UKZEdIhrrM2O0wU0D2C4bIGB4VxkFrASALxHlnnKs9KioAFvZ_q2TPRRrpGn4rWs.zL5PG7NCIwh5AlX8oFaeYw"))

    def test_short(self):
        self.assertFalse(is_valid_xboxlive_token("eyJhbGciOiJSU0EtT0FFUCIsImVuYyI6IkExMjhDQkMtSFMyNTYiLCJ6aXAiOiJERUYiLCJ4NXQiOiJxcEQtU2ZoOUg3NFFHOXlMN1hSZXJ5RmZvbk0iLCJjdHkiOiJKV1QifQ.D0sCUjRlzkM9VpLW3Yc3gOc85-Kc5E33Et8r-2NPr7Rc4vrGyYGB5OuyMzAJaZ0IkGHgJQkdjQr5e2lbNUHtWQ_a2KypTzmgA74ehEhPKRQdtiC-kkEDxgtC0ijPdL41EvBq_NMztD7yNwUA7i3a45OASqhB897vpEZaxBglYfThewDKAICOhkT4G6UJ2LRWjo2HrWnDHDTymzw_jXsUDorqLvGQTJg3DA.nOeKddrwqhpmGng2NWBNbA.Gc_0MiXpwU3MjtjJ2VPrQN_bKB279Ej0Fxnu1YxP0WAu2Qx8LtqEoSwTSWPnDCDLNr9ReOyWEtr_xsu_X1kvqGHjyHOEdPuYdfq-B4aKxkVYcgpEQYXM53A46kre8g9dmO3AxWqVe7-g2GtG59dY906AqcN7tjczAY0C8oQMaus2_m1rcoF1vEnm18_5XyRW-dR-H_7bN7nwdEBJRufQbHeYtGLkoTuP8B8T7s5QWL84Ijfg9fGbJpC2uqtWljZtNIR1SY_N462PRiMuyE9_ESWkmUUkDykRmPARWkzVkVQNaDich3f3N_QdabCszTwpi62_vwyVAzUSID8-J6sSaReWMRjyrIE6CcYDssafyEfBqRPawfuJYfJRt8vixeXoQhkEQlAl8fhifWa0zm5OXrhB5vP4M-R-NNwyxlxFsYfRf8H46JHiAbFRTMZdzURU9dQEoOmaKJCztRmSlUW4D9Q6XVEdPHS3CCV9H7VHO17_VxHEOegdUdd_vmtYPtbTgGaeJese2gjF9ZAh65T5mddFyYrAl3vSU65BD53gpjEQL3LmRbTIxGBHpnXp2UU96llBp8_Uwr-TzdQOLT8RzfJshssPMHKBLlGNL4ieyvryGK0Du1WL-uvfugI7mD4PReOsnw7E13WMvJhvXelLpvFv43mzFqREmcz2u4upPjfBUgmXpwHKdWTUxLhtsLSn9eOQ8s-2GWqqQKbM2BCRZGcx2RpCHSNJrLGy75D6Y2Yz0HkEB3LpSRz4cZlJEZsDOZpxvLk6tEHD3FFK09alyYJZBuISGtM4mMNbMqkSeh4aA2pHvpVCP_ef0p5HKPx-UKZEdIhrrM2O0wU0D2C4bIGB4VxkFrASALxHlnnKs9KioAFvZ_q2TPRRrpGn4rWs.zL5PG7NCIwh5AlX8oFaeYw"))

    def test_long(self):
        self.assertFalse(is_valid_xboxlive_token("eyJhbGciOiJSU0EtT0FFUCIsImVuYyI6IkExMjhDQkMtSFMyNTYiLCJ6aXAiOiJERUYiLCJ4NXQiOiJxcEQtU2ZoOUg3NFFHOXlMN1hSZXJ5RmZvbk0iLCJjdHkiOiJKV1QifQ.bQnxbQgQ9EF55A5d6X3R-D0sCUjRlzkM9VpLW3Yc3gOc85-Kc5E33Et8rkkEDxgtC0ijPdL41EvBqNMztD7yNwUA7i3a45OASqhB897vpEZaxBglYfThewDKAICOhkT4G6UJ2LRWjo2HrWnDHDTymzw_jXsUDorqLvGQTJg3DA.nOeKddrwqhpmGng2NWBNbA.Kc5E33Et8r-2NPr7Rc4vrGyYGB5OuyMzAJaZ0IkGHgJQkdjQr5e2lbNUHtWQ_a2KypTzmgA74ehEhPKRQdtiC-R9f8kf23BbEXJIKvjkraRUyNglOMUE3kKESlHQ35al71WDgAXvzGJ3ndEN1a4sK9kX6AjLOjv75huYI2eOtZk3eRlBQDyz-Kc5E33Et8rkkEDxgtC0ijPdL41EvBqNMztD7yNwUA7i3a45OASqhB897vpEZaxBglYfThewDKAICOhkT4G6UJ2LRWjo2HrWnDHDTymzw_jXsUDorqLvGQTJg3DA.nOeKddrwqhpmGng2NWBNbA.Gc_0MiXpwU3MjtjJ2VPrQN_bKB279Ej0Fxnu1YxP0WAu2Qx8LtqEoSwTSWPnDCDLNr9ReOyWEtr_xsu_X1kvqGHjyHOEdPuYdfq-wUltNQdjdrzqp6PRVk9mlmvXnXQJU7Uhyidg0tFmGF5S39YOqCfWhgnDzUIQe-B4aKxkVYcgpEQYXM53A46kre8g9dmO3AxWqVe7-g2GtG59dY906AqcN7tjczAY0C8oQMaus2_m1rcoF1vEnm18_5XyRW-dGc_0MiXpwU3MjtjJ2VPrQN_bKB279Ej0Fxnu1YxP0WAu2Qx8LtqEoSwTSWPnDCDLNr9ReOyWEtr_xsu_X1kvqGHjyHOEdPuYdfqR-S1S7E0Rt4v8pzLfrDwwdpXR_LhnKce2zCM_UHzkvXnwUKOqns3KcUnip3ibGR51uQ-UKZEdIhrrM2O0wU0D2C4bIGB4VxkFrASALxHlnnKs9KioAFvZ_q2TPRRrpGn4rWs.H_7bN7nwdEBJRufQbHeYtGLkoTuP8B8T7s5QWL84Ijfg9fGbJpC2uqtWljZtNIR1SY_N462PRiMuyE9_ESWkmUUkDykRmPARWkzVkVQNaDich3f3N_QdabCszTwpi62_vwyVAzUSID8-J6sSaReWMRjyrIE6CcYDssafyEfBqRPawfuJYfJRt8vixeXoQhkEQlAl8fhifWa0zm5OXrhB5vP4M-R-NNwyxlxFsYfRf8H46JHiAbFRTMZdzURU9dQEoOmaKJCztRmSlUW4D9Q6XVEdPHS3CCV9H7VHO17_VxHEOegdUdd_vmtYPtbTgGaeJese2gjF9ZAh65T5mddFyYrAl3vSU65BD53gpjEQL3LmRbTIxGBHpnXp2UU96llBp8_Uwr-TzdQOLT8RzfJshssPMHKBLlGNL4ieyvryGK0Du1WL-uvfugI7mD4PReOsnw7E13WMvJhvXelLpvFv43mzFqREmcz2u4upPjfBUgmXpwHKdWTUxLhtsLSn9eOQ8s-2NNwyxlxFsYfRf8H46JHiAbFRTMZdzURU9dQEoOmaKJCztRmSlUW4D9Q6XVEdPHS3CCV9H7VHO17_VxHEOegdUdd_vmtYPtbTgGaeJese2gjF9ZAh65T5mddFyYrAl3vSU65BD53gpjEQL3LmRbTIxGBHpnXp2UU96llBp8_UwrGWqqQKbM2BCRZGcx2RpCHSNJrLGy75D6Y2Yz0HkEB3LpSRz4cZlJEZsDOZpxvLk6tEHD3FFK09alyYJZBuISGtM4mMNbMqkSeh4aA2pHvpVCP_ef0p5HKPx-UKZEdIhrrM2O0wU0D2C4bIGB4VxkFrASALxHlnnKs9KioAFvZ_q2TPRRrpGn4rWs.zL5PG7NCIwh5AlX8oFaeYw"))


    def test_wrong(self):
        self.assertFalse(is_valid_xboxlive_token("eyJhbGciOiJSU0EtT0FFUCIsImVuYyI6IkExMjhDQkMtSFMyNTYiLCJ6aXAiOiJERUYiLCJ4NXQiOiJxcEQtU2ZoOUg3NFFHOXlMN1hSZXJ5RmZvbk0iLCJjdHkiOiJKV1QifQ!bQnxbQgQ9EF55A5d6X3R-D0sCUjRlzkM9VpLW3Yc3gOc85-Kc5E33Et8r-2NPr7Rc4vrGyYGB5OuyMzAJaZ0IkGHgJQkdjQr5e2lbNUHtWQ_a2KypTzmgA74ehEhPKRQdtiC-R9f8kf23BbEXJIKvjkraRUyNglOMUE3kKESlHQ35al71WDgAXvzGJ3ndEN1a4sK9kX6AjLOjv75huYI2eOtZk3eRlBQDyz-kkEDxgtC0ijPdL41EvBq_NMztD7yNwUA7i3a45OASqhB897vpEZaxBglYfThewDKAICOhkT4G6UJ2LRWjo2HrWnDHDTymzw_jXsUDorqLvGQTJg3DA!nOeKddrwqhpmGng2NWBNbA!Gc_0MiXpwU3MjtjJ2VPrQN_bKB279Ej0Fxnu1YxP0WAu2Qx8LtqEoSwTSWPnDCDLNr9ReOyWEtr_xsu_X1kvqGHjyHOEdPuYdfq-wUltNQdjdrzqp6PRVk9mlmvXnXQJU7Uhyidg0tFmGF5S39YOqCfWhgnDzUIQe-B4aKxkVYcgpEQYXM53A46kre8g9dmO3AxWqVe7-g2GtG59dY906AqcN7tjczAY0C8oQMaus2_m1rcoF1vEnm18_5XyRW-dR-S1S7E0Rt4v8pzLfrDwwdpXR_LhnKce2zCM_UHzkvXnwUKOqns3KcUnip3ibGR51uQ-H_7bN7nwdEBJRufQbHeYtGLkoTuP8B8T7s5QWL84Ijfg9fGbJpC2uqtWljZtNIR1SY_N462PRiMuyE9_ESWkmUUkDykRmPARWkzVkVQNaDich3f3N_QdabCszTwpi62_vwyVAzUSID8-J6sSaReWMRjyrIE6CcYDssafyEfBqRPawfuJYfJRt8vixeXoQhkEQlAl8fhifWa0zm5OXrhB5vP4M-R-NNwyxlxFsYfRf8H46JHiAbFRTMZdzURU9dQEoOmaKJCztRmSlUW4D9Q6XVEdPHS3CCV9H7VHO17_VxHEOegdUdd_vmtYPtbTgGaeJese2gjF9ZAh65T5mddFyYrAl3vSU65BD53gpjEQL3LmRbTIxGBHpnXp2UU96llBp8_Uwr-TzdQOLT8RzfJshssPMHKBLlGNL4ieyvryGK0Du1WL-uvfugI7mD4PReOsnw7E13WMvJhvXelLpvFv43mzFqREmcz2u4upPjfBUgmXpwHKdWTUxLhtsLSn9eOQ8s-2GWqqQKbM2BCRZGcx2RpCHSNJrLGy75D6Y2Yz0HkEB3LpSRz4cZlJEZsDOZpxvLk6tEHD3FFK09alyYJZBuISGtM4mMNbMqkSeh4aA2pHvpVCP_ef0p5HKPx-UKZEdIhrrM2O0wU0D2C4bIGB4VxkFrASALxHlnnKs9KioAFvZ_q2TPRRrpGn4rWs!zL5PG7NCIwh5AlX8oFaeYw"))

class TestXSTSTok(unittest.TestCase):

    def test_simple1(self):
        self.assertTrue(is_valid_xsts_token("eyJlbmMiOiJBMTI4Q0JDLUhTMjU2IiwiYWxnIjoiUlNBLU9BTVAiLCJjdHkiOiJKV7QiLCJ6aXAiOiJETUYiLCJ4NXQiOiJnN3hlanVTXzTnOXNNdW9fLXdVeFQ5NHNHancifQ.cdk6FBclbS_pzo6hn6GWa2V789G5OYpAwPTTWYTTdwdca_X7rT5Eikb7vv49WkBjjjesGU2q4e2_BAVOre7FT4-TrSxn9zxDxviCsVvwoA4bxP9_rSqjEhksFmi_kJCP74F4h3HVOo9bLMjzYVjhdv8iTnG3jTPhC9U_ab6TlD3TH8u3taiHVoIfcyE_CXpFCvD9Uwnd35MnjF82ic7YfnP0s_8GPcqs-VYdH0wLS7E_nNFKxTz3q3fpxXnn_EdpIYbU-UqBrb2H3xONg0gTrXWSDXGF-8IMycv7n6IIVc8CzIOC7DOlhE6lj54qk9pfY25qOg9co3BYIAAVM2dbVw.iywYrDTgQGwI3ulhnmyDVw.LpxJltzPS2X_N66GPNA792OpPriKeq4YECcgdCbTTisXbHX9-62vef4DxdEuGGT4zBgJrOhICI55rpTsbWjYkg7smJxQdpAmlUJz5STTzTyh7T5ICjTQGi9WFQESqFbwQbSGyT6AuVwitZ42T46-aCx_cqpLvQ3h0LXnva7obEp3USJT-hU3yh52B4vmbG7bTtOFdBoT8aBnk6nsSHyk3YFVv3TuvLqdTD6Pz2i_B9_Ku3o08o5y9LvB6Bf_ZxVEikZbm89Gl6V5d66sbnfU2xloCHcXKVEuJQoThjgQ2pWrml-_TyZqtV4W6C6xYlBMZloJzQGQ6izquShsrUj0HxN6uBQ7BbQZZTclPCwxcp3qsJTLH4nWEbK8JsTz2AfSxBdscLfuzyTSyW4JDtUkCUt9BbY_4OqTaM29reb3ww6v-k9KCBdJarOlWgrIjIYjb3urTe32aBjIPgL6gwoVxAnMQGp00Odk9tWqb7gAqqg4v87GC8GSciZV_DmbxxMXLZ9SUF4M0ftAJIn_02NOtnlJxzrQT4_Uc7P84XlmKchN6zStdMoqnYFTbmLBrSt9Wq94NIE6ZryoZydtSTqL6rqzdbys7QhbVPjSWAF8aDL7vgmdBdyu7pK8pOCWZ8oegP84_Q5PsBeLg_gQESHdzOcaUOpVwAuI5D80E9hsY-EWGvDKJCvwjGSb5nex7mcB6MUPw_MoFsqc6T3YuCQeUNvszza6jIbFfcY-D4Tg73hkbb7ksmXVlVjyZyHm-MULGrKsfJL7-JGMhL5XaHL8haqzq77p6wTuyDtYFs0A3N85jpntFCeLifi2EP3TwuDvquETrEYUQy7PhPlPznxYn-63Gq3V7395owGBjTs0bq7fjFBNyOUajIxrMkqezBBXZb02LBztB7ic9dwlIx7khzx-z6AdpcoASV7hV2jbE59NYkg4VjNW2xjm9296HxuQ_8JSuiNSYDVJOjoMUKftvM60U_jTypUv5JAj9Ky9O7M3qKB9ydzjTp5EGa7JCXTwmmGP5LyGg7DsST6dPmrjTT7tLiVr7wzk7VrqvODzGvIr-JD7r0zVOVzXbWgHk5NZH5UkVbhmYCX-OpWwrI0NK7uw7u_wZOTb-K5gMpYMQIYlWETwX4PLIw4oKcrJtoAaDzzZo9Th8TriSMSL7CZiFdF0grwp6Gb9hc_ASCnLJfoYms8-pNIFXyH4kz-ThI4IYqCcL-jFnjdFUhKmNnMt7SvqUZsizOThTALVA-O-4Pge77o5U7cbPyrvWYQTQ27WBocK9woypOQKkpSdeCuwuDL9lTTKa7yoe7V5iGIEAPcGUwbeIW0JEFqTdbSTnFMweFWM2k4rwFNMffntqThX4JZHW8SsEmbMfN_mVGeWv7HFdpPx_P4vDBTrSSzNNHJPhJxjCmXb8zWr6od9pCYA9r3K8xMuXk9ZHHYwrNv-xHKh2kgD_xuqW6PerpY3aAKY9cB23gQPhkOYCCQ9t_PcCIQE2ADydmssWGl8PSAYFMajNVxpSY-2nqIxlBlKWrQlOK5Da8-wz5T5Lsf9aSjUasdNTTybxMPDd2-msarSAq9OrJKnpMoI7IfCeTVKFVzlh53LxfOocfQe7oxWtTd96UkPWMCcZCGvcbNhEODhodWwWuweEYA0A2h05jdXkvIs.TxDkb4lI5y0WXeXLn_xVkA"))

    def test_short(self):
        self.assertFalse(is_valid_xsts_token("eyJlbmMiOiJBMTI4Q0JDLUhTMjU2IiwiYWxnIjoiUlNBLU9BTVAiLCJjdHkiOiJKV7QiLCJ6aXAiOiJETUYiLCJ4NXQiOiJnN3hlanVTXzTnOXNNdW9fLXdVeFQ5NHNHancifQ.cdk6FBclbS_pzo6hn6GWa2V789G5OYpAwPTTWYTTdwdca_X7rT5Eikb7vv49WkBjjjesGU2q4e2_BAVOre7FT4-TrSxn9zxDxviCsVvwoA4bxP9_rSqjEhksFmi_kJCP74F4h3HVOo9bLMjzYVjhdv8iTnG3jTPhC9U_ab6TlD3TH8u3taiHVoIfcyE_CXpFCvD9Uwnd35MnjF82ic7YfnP0s_8GPcqs-VYdH0wLS7E_nNFKxTz3q3fpxXnn_EdpIYbU-UqBrb2H3xONg0gTrXWSDXGF-8IMycv7n6IIVc8CzIOC7DOlhE6lj54qk9pfY25qOg9co3BYIAAVM2dbVw.LpxJltzPS2X_N66GPNA792OpPriKeq4YECcgdCbTTisXbHX9-62vef4DxdEuGGT4zBgJrOhICI55rpTsbWjYkg7smJxQdpAmlUJz5STTzTyh7T5ICjTQGi9WFQESqFbwQbSGyT6AuVwitZ42T46-aCx_cqpLvQ3h0LXnva7obEp3USJT-hU3yh52B4vmbG7bTtOFdBoT8aBnk6nsSHyk3YFVv3TuvLqdTD6Pz2i_B9_Ku3o08o5y9LvB6Bf_ZxVEikZbm89Gl6V5d66sbnfU2xloCHcXKVEuJQoThjgQ2pWrml-k9KCBdJarOlWgrIjIYjb3urTe32aBjIPgL6gwoVxAnMQGp00Odk9tWqb7gAqqg4v87GC8GSciZV_DmbxxMXLZ9SUF4M0ftAJIn_02NOtnlJxzrQT4_Uc7P84XlmKchN6zStdMoqnYFTbmLBrSt9Wq94NIE6ZryoZydtSTqL6rqzdbys7QhbVPjSWAF8aDL7vgmdBdyu7pK8pOCWZ8oegP84_Q5PsBeLg_gQESHdzOcaUOpVwAuI5D80E9hsY-EWGvDKJCvwjGSb5nex7mcB6MUPw_MoFsqc6T3YuCQeUNvszza6jIbFfcY-D4Tg73hkbb7ksmXVlVjyZyHm-MULGrKsfJL7-JGMhL5XaHL8haqzq77p6wTuyDtYFs0A3N85jpntFCeLifi2EP3TwuDvquETrEYUQy7PhPlPznxYn-63Gq3V7395owGBjTs0bq7fjFBNyOUajIxrMkqezBBXZb02LBztB7ic9dwlIx7khzx-JD7r0zVOVzXbWgHk5NZH5UkVbhmYCX-OpWwrI0NK7uw7u_wZOTb-K5gMpYMQIYlWETwX4PLIw4oKcrJtoAaDzzZo9Th8TriSMSL7CZiFdF0grwp6Gb9hc_ASCnLJfoYms8-pNIFXyH4kz-ThI4IYqCcL-jFnjdFUhKmNnMt7SvqUZsizOThTALVA-O-4Pge77o5U7cbPyrvWYQTQ27WBocK9woypOQKkpSdeCuwuDL9lTTKa7yoe7V5iGIEAPcGUwbeIW0JEFqTdbSTnFMweFWM2k4rwFNMffntqThX4JZHW8SsEmbMfN_mVGeWv7HFdpPx_P4vDBTrSSzNNHJPhJxjCmXb8zWr6od9pCYA9r3K8xMuXk9ZHHYwrNv-xHKh2kgD_xuqW6PerpY3aAKY9cB23gQPhkOYCCQ9t_PcCIQE2ADydmssWGl8PSAYFMajNVxpSY-2nqIxlBlKWrQlOK5Da8-wz5T5Lsf9aSjUasdNTTybxMPDd2-msarSAq9OrJKnpMoI7IfCeTVKFVzlh53LxfOocfQe7oxWtTd96UkPWMCcZCGvcbNhEODhodWwWuweEYA0A2h05jdXkvIs.TxDkb4lI5y0WXeXLn_xVkA"))

    def test_long(self):
        self.assertFalse(is_valid_xsts_token("eyJlbmMiOiJBMTI4Q0JDLUhTMjU2IiwiYWxnIjoiUlNBLU9BTVAiLCJjdHkiOiJKV7QiLCJ6aXAiOiJETUYiLCJ4NXQiOiJnN3hlanVTXzTnOXNNdW9fLXdVeFQ5NHNHancifQ.-62vef4DxdEuGGT4zBgJrOhICI55rpTsbWjYkg7smJxQdpAmlUJz5STTzTyh7T5ICjTQGi9WFQESqFbwQbSGyT6AuVwitZ42T46cdk6FBclbS_pzo6hn6GWa2V789G5OYpAwPTTWYTTdwdca_X7rT5Eikb7vv49WkBjjjesGU2q4e2_BAVOre7FT4-TrSxn9zxDxviCsVvwoA4bxP9_rSqjEhksFmi_kJCP74F4h3HVOo9bLMjzYVjhdv8iTnG3jTPhC9U_ab6TlD3TH8u3taiHVoIfcyE_CXpFCvD9Uwnd35MnjF82ic7YfnP0s_8GPcqs-VYdH0wLS7E_nNFKxTz3q3fpxXnn_EdpIYbU-UqBrb2H3xONg0gTrXWSDXGF-8IMycv7n6IIVc8CzIOC7DOlhE6lj54qk9pfY25qOg9co3BYIAAVM2dbVw.iywYrDTgQGwI3ulhnmyDVw.LpxJltzPS2X_N66GPNA792OpPriKeq4YECcgdCbTTisXbHX9-62vef4DxdEuGGT4zBgJrOhICI55rpTsbWjYkg7smJxQdpAmlUJz5STTzTyh7T5ICjTQGi9WFQESqFbwQbSGyT6AuVwitZ42T46-MULGrKsfJL7-JGMhL5XaHL8haqzq77p6wTuyDtYFs0A3N85jpntFCeLifi2EP3TwuDvquETrEYUQy7PhPlPznxYnaCx_cqpLvQ3h0LXnva7obEp3USJT-hU3yh52B4vmbG7bTtOFdBoT8aBnk6nsSHyk3YFVv3TuvLqdTD6Pz2i_B9_Ku3o08o5y9LvB6Bf_ZxVEikZbm89Gl6V5d66sbnfU2xloCHcXKVEuJQoThjgQ2pWrml-_TyZqtV4W6C6xYlBMZloJzQGQ6izquShsrUj0HxN6uBQ7BbQZZTclPCwxcp3qsJTLH4nWEbK8JsTz2AfSxBdscLfuzyTSyW4JDtUkCUt9BbY_4OqTaM29reb3ww6v-k9KCBdJarOlWgrIjIYjb3urTe32aBjIPgL6gwoVxAnMQGp00Odk9tWqb7gAqqg4v87GC8GSciZV_DmbxxMXLZ9SUF4M0ftAJIn_02NOtnlJxzrQT4_Uc7P84XlmKchN6zStdMoqnYFTbmLBrSt9Wq94NIE6ZryoZydtSTqL6rqzdbys7QhbVPjSWAF8aDL7vgmdBdyu7pK8pOCWZ8oegP84_Q5PsBeLg_gQESHdzOcaUOpVwAuI5D80E9hsY-EWGvDKJCvwjGSb5nex7mcB6MUPw_MoFsqc6T3YuCQeUNvszza6jIbFfcY-D4Tg73hkbb7ksmXVlVjyZyHm-M2nqIxlBlKWrQlOK5Da8-wz5T5Lsf9aSjUasdNTTybxMPDd2ULGrKsfJL7-JGMhL5XaHL8haqzq77p6wTuyDtYFs0A3N85jpntFCeLifi2EP3TwuDvquETrEYUQy7PhPlPznxYn-63Gq3V7395owGBjTs0bq7fjFBNyOUajIxrMkqezBBXZb02LBztB7ic9dwlIx7khzx-z6AdpcoASV7hV2jbE59NYkg4VjNW2xjm9296HxuQ_8JSuiNSYDVJOjoMUKftvM60U_jTypUv5JAj9Ky9O7M3qKB9ydzjTp5EGa7JCXTwmmGP5LyGg7DsST6dPmrjTT7tLiVr7wzk7VrqvODzGvIr-JD7r0zVOVzXbWgHk5NZH5UkVbhmYCX-OpWwrI0NK7uw7u_wZOTb-K5gMpYMQIYlWETwX4PLIw4oKcrJtoAaDzzZo9Th8TriSMSL7CZiFdF0grwp6Gb9hc_ASCnLJfoYms8-pNIFXyH4kz-ThI4IYqCcL-jFnjdFUhKmNnMt7SvqUZsizOThTALVA-O-4Pge77o5U7cbPyrvWYQTQ27WBocK9woypOQKkpSdeCuwuDL9lTTKa7yoe7V5iGIEAPcGUwbeIW0JEFqTdbSTnFMweFWM2k4rwFNMffntqThX4JZHW8SsEmbMfN_mVGeWv7HFdpPx_P4vDBTrSSzNNHJPhJxjCmXb8zWr6od9pCYA9r3K8xMuXk9ZHHYwrNv-iywYrDTgQGwI3ulhnmyDVw.LpxJltzPS2X_N66GPNA792OpPriKeq4YECcgdCbTTisXbHX9-x-z6AdpcoASV7hV2jbE59NYkg4VjNW2xjm9296HxuQ_8JSuiNSYDVJOjoMUKftvM60U_jTypUv5JAj9Ky9O7M3qKB9ydzjTp5EGa7JCXTwmmGP5LyGg7DsST6dPmrjTT7tLiVr7wzk7VrqvODzGvIr-HKh2kgD_xuqW6PerpY3aAKY9cB23gQPhkOYCCQ9t_PcCIQE2ADydmssWGl8PSAYFMajNVxpSY-2nqIxlBlKWrQlOK5Da8-wz5T5Lsf9aSjUasdNTTybxMPDd2-msarSAq9OrJKnpMoI7IfCeTVKFVzlh53LxfOocfQe7oxWtTd96UkPWMCcZCGvcbNhEODhodWwWuweEYA0A2h05jdXkvIs.TxDkb4lI5y0WXeXLn_xVkA"))

    def test_wrong(self):
        self.assertTrue(is_valid_xsts_token("eyJlbmMiOiJBMTI4Q0JDLUhTM:U2IiwiYWxnI:oiUlNBLU9BTVAiLCJ:dHkiOiJKV7QiLCJ6aXAiOiJETUYiLCJ4NXQiOiJnN3hlanVTXzTnOXNNdW9fLXdVeFQ5NHNHancifQ.cdk6FBclbS_pzo6hn6GWa2V789G5OYpAwPTTWYTTdwdca_X7rT5Eikb7vv49WkB:::esGU2q4e2_BAVOre7FT4-TrSxn9zxDxviCsVvwoA4bxP9_rSq:EhksFmi_kJCP74F4h3HVOo9bLM:zYV:hdv8iTnG3:TPhC9U_ab6TlD3TH8u3taiHVoIfcyE_CXpFCvD9Uwnd35Mn:F82ic7YfnP0s_8GPcqs-VYdH0wLS7E_nNFKxTz3q3fpxXnn_EdpIYbU-UqBrb2H3xONg0gTrXWSDXGF-8IMycv7n6IIVc8CzIOC7DOlhE6l:54qk9pfY25qOg9co3BYIAAVM2dbVw.iywYrDTgQGwI3ulhnmyDVw.LpxJltzPS2X_N66GPNA792OpPriKeq4YECcgdCbTTisXbHX9-62vef4DxdEuGGT4zBgJrOhICI55rpTsbW:Ykg7smJxQdpAmlUJz5STTzTyh7T5IC:TQGi9WFQESqFbwQbSGyT6AuVwitZ42T46-aCx_cqpLvQ3h0LXnva7obEp3USJT-hU3yh52B4vmbG7bTtOFdBoT8aBnk6nsSHyk3YFVv3TuvLqdTD6Pz2i_B9_Ku3o08o5y9LvB6Bf_ZxVEikZbm89Gl6V5d66sbnfU2xloCHcXKVEuJQoTh:gQ2pWrml-_TyZqtV4W6C6xYlBMZloJzQGQ6izquShsrU:0HxN6uBQ7BbQZZTclPCwxcp3qsJTLH4nWEbK8JsTz2AfSxBdscLfuzyTSyW4JDtUkCUt9BbY_4OqTaM29reb3ww6v-k9KCBdJarOlWgrI:IY:b3urTe32aB:IPgL6gwoVxAnMQGp00Odk9tWqb7gAqqg4v87GC8GSciZV_DmbxxMXLZ9SUF4M0ftAJIn_02NOtnlJxzrQT4_Uc7P84XlmKchN6zStdMoqnYFTbmLBrSt9Wq94NIE6ZryoZydtSTqL6rqzdbys7QhbVP:SWAF8aDL7vgmdBdyu7pK8pOCWZ8oegP84_Q5PsBeLg_gQESHdzOcaUOpVwAuI5D80E9hsY-EWGvDKJCvw:GSb5nex7mcB6MUPw_MoFsqc6T3YuCQeUNvszza6:IbFfcY-D4Tg73hkbb7ksmXVlV:yZyHm-MULGrKsfJL7-JGMhL5XaHL8haqzq77p6wTuyDtYFs0A3N85:pntFCeLifi2EP3TwuDvquETrEYUQy7PhPlPznxYn-63Gq3V7395owGB:Ts0bq7f:FBNyOUa:IxrMkqezBBXZb02LBztB7ic9dwlIx7khzx-z6AdpcoASV7hV2:bE59NYkg4V:NW2x:m9296HxuQ_8JSuiNSYDVJO:oMUKftvM60U_:TypUv5JA:9Ky9O7M3qKB9ydz:Tp5EGa7JCXTwmmGP5LyGg7DsST6dPmr:TT7tLiVr7wzk7VrqvODzGvIr-JD7r0zVOVzXbWgHk5NZH5UkVbhmYCX-OpWwrI0NK7uw7u_wZOTb-K5gMpYMQIYlWETwX4PLIw4oKcrJtoAaDzzZo9Th8TriSMSL7CZiFdF0grwp6Gb9hc_ASCnLJfoYms8-pNIFXyH4kz-ThI4IYqCcL-:Fn:dFUhKmNnMt7SvqUZsizOThTALVA-O-4Pge77o5U7cbPyrvWYQTQ27WBocK9woypOQKkpSdeCuwuDL9lTTKa7yoe7V5iGIEAPcGUwbeIW0JEFqTdbSTnFMweFWM2k4rwFNMffntqThX4JZHW8SsEmbMfN_mVGeWv7HFdpPx_P4vDBTrSSzNNHJPhJx:CmXb8zWr6od9pCYA9r3K8xMuXk9ZHHYwrNv-xHKh2kgD_xuqW6PerpY3aAKY9cB23gQPhkOYCCQ9t_PcCIQE2ADydmssWGl8PSAYFMa:NVxpSY-2nqIxlBlKWrQlOK5Da8-wz5T5Lsf9aS:UasdNTTybxMPDd2-msarSAq9OrJKnpMoI7IfCeTVKFVzlh53LxfOocfQe7oxWtTd96UkPWMCcZCGvcbNhEODhodWwWuweEYA0A2h05:dXkvIs.TxDkb4lI5y0WXeXLn_xVkA"))

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
