import unittest

import libmorse


DEBUG = True


class TestMorseTranslator(unittest.TestCase):

    def setUp(self):
        self.translator = libmorse.MorseTranslator(debug=DEBUG)

    def tearDown(self):
        self.translator.close()

    def _test_signals(self, mor_file):
        mor_code = libmorse.get_mor_code(mor_file)
        for signal in mor_code:
            self.translator.put(signal)
        self.translator.wait()
        results = []
        while True:
            try:
                result = self.translator.get(block=False)
            except libmorse.TranslatorMorseError:
                break
            results.append(result)
        return results

    def test_basic_signals(self):
        results = self._test_signals("basic.mor")
        print(results)
