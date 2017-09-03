import unittest

import mock

import libmorse


DEBUG = True


class TestMorseTranslator(unittest.TestCase):

    # Morse code resources.
    MORSE = {
        "basic.mor": [
            "-- --- .-. ... . / -.-. --- -.. .",
            "MORSE CODE"
        ],
        "basic_noise.mor": [
            "-- --- .-. ... . / -.-. --- -.. .",
            "MORSE CODE"
        ],
    }

    def setUp(self):
        self.translator = libmorse.MorseTranslator(debug=DEBUG)

    def tearDown(self):
        self.translator.close()

    def _send_mor_code(self, mor_code):
        for signal in mor_code:
            self.translator.put(signal)
        self.translator.wait()

    def _get_translation(self, mor_file, get_alphabet=True):
        mor_code = libmorse.get_mor_code(mor_file)
        if get_alphabet:
            self._send_mor_code(mor_code)
        else:
            with mock.patch("libmorse.translator.MorseTranslator."
                            "_parse_morse_code") as mock_parse:
                def parse():
                    code = self.translator._morse_code[:]
                    self.translator._morse_code = []
                    return code
                mock_parse.side_effect = parse
                self._send_mor_code(mor_code)

        results = []
        while True:
            try:
                result = self.translator.get(block=False)
            except libmorse.TranslatorMorseError:
                break
            results.append(result)

        return results

    def _test_alphamorse(self, name, test_alphabet=True):
        translation = self._get_translation(
            name,
            get_alphabet=test_alphabet
        )
        result = "".join(translation).strip()
        if not test_alphabet:
            result = result.strip(" /")

        expected = self.MORSE[name][int(test_alphabet)]
        self.assertEqual(expected, result)

    def test_basic_morse(self):
        self._test_alphamorse("basic.mor", test_alphabet=False)

    def test_basic_alphabet(self):
        self._test_alphamorse("basic.mor", test_alphabet=True)

    def test_basic_noise_morse(self):
        self._test_alphamorse("basic_noise.mor", test_alphabet=False)

    def test_basic_noise_alphabet(self):
        self._test_alphamorse("basic_noise.mor", test_alphabet=True)
