import unittest

import libmorse


class TestMorse(unittest.TestCase):

    def test_basic(self):
        data = libmorse.get_res_content("basic.mor")
        mor_code = libmorse.get_mor_code(data)
        self.assertEqual(47, len(mor_code))
